#!/usr/bin/env python3

# folium icons: https://fontawesome.com/icons?d=gallery
# folium icon colors: ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
# folium tiles: OpenStreetMap , Stamen Terrain, Stamen Toner

def import_libraries(libraries):
    """
    Helps load/install required libraries when running from cmd prompt

    Returns
    -------
    None.

    """
    import subprocess, warnings
    warnings.filterwarnings("ignore")
    exec('warnings.filterwarnings("ignore")')
    aliases = {'numpy':'np','pandas':'pd','matplotlib.pyplot':'plt',
               'branca.colormap':'cm','haversine':'hs'}
    for s in libraries:
        try:
            exec(f"import {s[0]} as {aliases[s[0]]}") if s[0] in list(aliases.keys()) else exec(f"import {s[0]}")
        except ImportError:
            print(f'Installing... {s[0].split(".")[0]}')
            cmd = f'python -m pip install {s[0].split(".")[0]}'
            subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
        if len(s) == 1: continue
        for sl in s[1]:
            exec(f'from {s[0]} import {sl}')

libraries = [['math',['sin','cos','pi']],['collections',['defaultdict']],
             ['branca.colormap'],['datetime',['date']],['jinja2'],['numpy'],
             ['warnings'],['mgrs'],['haversine'],['haversine',['Unit']],
             ['sympy',['Point','Polygon']],['folium']]

import_libraries(libraries)
import folium
import branca.colormap as cm
from collections import defaultdict
import numpy as np
import warnings
import mgrs
from sympy import Point, Polygon
import alive_progress
from alive_progress import alive_bar
import os
import pandas as pd
import shutil
import os
import requests
warnings.filterwarnings("ignore")

def is_port_in_use(port: int) -> bool:
    """
    Assesses if there's an active service on a specified port

    Parameters:
    ----------
    port : int
        Port number of specified port
    
    Returns:
    ----------
    status : bool
        Boolean status of port availability (TRUE = not in use)

    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        status = s.connect_ex(('localhost', port)) == 0
        return status
    
def check_internet_connection():
    """
    Assesses connectivity to the public internet

    Parameters:
    ----------
    None
    
    Returns:
    ----------
    status : bool
        Boolean status of public internet connectivity (TRUE = connected)
        
    """
    from urllib import request
    try:
        request.urlopen('http://8.8.8.8', timeout=1)
        return True
    except request.URLError as err: 
        return False
    except TimeoutError:
        return False

def convert_coordinates_to_meters(coord):
    """
    Converts coodinate distance to meters.

    Parameters
    ----------
    meters : float
        Length in meters.

    Returns
    -------
    float
        Length in coordinates.

    """
    assert isinstance(coord,(float,int)), 'Input needs to be a float.'
    return coord * 111139

def adjust_coordinate(starting_coord,azimuth_degrees,shift_m):
    """
    Adjusts input lat-lon coordinate a specified distance in a specified direction

    Parameters:
    ----------
    starting_coord : list
        Coordinate from which adjustments are applied in [lat,lon] format
    azimuth_degrees : float
        Angle of desired adjustment between 0 and 360 degrees
    shift_m : float
        Distance of desired adjustment in meters
    
    Returns:
    ----------
    new_coord : list
        Adjusted coordinate based on input in [lat,lon] format
        
    """
    import math
    assert isinstance(starting_coord,list) and len(starting_coord) == 2, 'Coordinate [lat,lon] needs to be a list of length 2.'
    assert isinstance(shift_m,(float,int)) and shift_m >= 10, 'Adjustment needs to be a float of at least 10m.'
    assert isinstance(azimuth_degrees,(float,int)) and 0 <= azimuth_degrees <= 360, 'Adjustment needs to be a float betwneen 0 and 360.'
    def func(degrees, magnitude): # returns in lat,lon format
        return magnitude * math.cos(math.radians(degrees)), magnitude * math.sin(math.radians(degrees))
    earth_radius_meters = 6371000.0
    starting_lat = float(starting_coord[0]); starting_lon = float(starting_coord[1])
    lat_adjustment_m, lon_adjustment_m = func(azimuth_degrees,shift_m)
    new_lat = starting_lat  + (lat_adjustment_m / earth_radius_meters) * (180 / math.pi)
    new_lon = starting_lon + (lon_adjustment_m / earth_radius_meters) * (180 / math.pi) / math.cos(starting_lat * math.pi/180)
    new_coord = [new_lat,new_lon]
    return new_coord

def convert_watts_to_dBm(p_watts):
    """
    Converts watts to dBm.

    Parameters
    ----------
    p_watts : float
        Power in watts (W).

    Returns
    -------
    float
        Power in dBm.

    """
    assert isinstance(p_watts,(float,int)) and p_watts >= 0, 'Wattage needs to be a float greater than zero.'
    return 10*np.log10(1000*p_watts)

def convert_coords_to_mgrs(coords,precision=5):
    """
    Convert location from coordinates to MGRS.

    Parameters
    ----------
    coords : list of length 2
        Grid coordinate. Example: [lat,long].
    precision : int, optional
        Significant figures per easting/northing value. The default is 5.

    Returns
    -------
    str
        Location in MGRS notation.

    """
    assert isinstance(coords,list), 'Coordinate input must be a list.'
    assert len(coords) == 2, 'Coordinate input must be of length 2.'
    return mgrs.MGRS().toMGRS(coords[0], coords[1],MGRSPrecision=precision)

def convert_mgrs_to_coords(milGrid):
    """
    Convert location from MGRS to coordinates.

    Parameters
    ----------
    milGrid : str
        Location in MGRS notation.

    Returns
    -------
    list
        Grid coordinate. Example: [lat,long].

    """
    assert isinstance(milGrid,str), 'MGRS must be a string'
    return list(mgrs.MGRS().toLatLon(milGrid.encode()))

def covert_degrees_to_radians(degrees):
    """
    Converts angle from degrees to radians.

    Parameters
    ----------
    degrees : float [0-360]
        Angle measured in degrees.

    Returns
    -------
    float
        Angle measured in radians [0-2π].

    """
    assert isinstance(degrees,(float,int)), 'Degrees must be a float [0-360]'
    return (degrees%360) * np.pi/180

def get_distance_between_coords(coord1,coord2):
    """
    Determines distance between two coordinates in meters

    Parameters
    ----------
    coord1 : list of length 2
        Grid coordinate. Example: [lat,long].
    coord2 : list of length 2
        Grid coordinate. Example: [lat,long].
    Returns
    -------
    float
        Distance between two coordinates in meters.

    """
    import haversine
    if isinstance(coord1,tuple):
        coord1 = list(coord1)
    if isinstance(coord2,tuple):
        coord2 = list(coord2)        
    # assert isinstance(coord1,list), 'Coordinate 1 must be a list.'
    assert len(coord1) == 2, 'Coordinate 1 must be of length 2.'
    # assert isinstance(coord2,list), 'Coordinate 2 must be a list.'
    assert len(coord2) == 2, 'Coordinate 2 must be of length 2.'
    return haversine.haversine(coord1,coord2,unit=haversine.Unit.METERS)

def get_center_coord(coord_list):
    """
    Returns the average coordinate from list of coordinates.

    Parameters
    ----------
    coord_list : list comprehension of length n
        List of coordinates. Example: [[lat1,long1],[lat2,long2]]

    Returns
    -------
    list
        Center coordiante.

    """
    assert isinstance(coord_list,list) and len(coord_list) >= 1, "Coordinates must be in a list comprehension of length 1 or greater"
    return [np.average([c[0] for c in coord_list]),np.average([c[1] for c in coord_list])]

def emission_distance(P_t_watts,f_MHz,G_t,G_r,R_s,path_loss_coeff=3):
    """
    Returns theoretical maximum distance of emission.

    Parameters
    ----------
    P_t_watts : float
        Power output of transmitter in watts (W).
    f_MHz : float
        Operating frequency in MHz.
    G_t : float
        Transmitter antenna gain in dBi.
    G_r : float
        Receiver antenna gain in dBi.
    R_s : float
        Receiver sensitivity in dBm *OR* power received in dBm.
    path_loss_coeff : float, optional
        Coefficient that considers partial obstructions such as foliage. 
        The default is 3.

    Returns
    -------
    float
        Theoretical maximum distance in km.

    """
    return 10**((convert_watts_to_dBm(P_t_watts)+(G_t-2.15)-32.4-(10*path_loss_coeff*np.log10(f_MHz))+(G_r-2.15)-R_s)/(10*path_loss_coeff))

def emission_optical_maximum_distance(t_h,r_h):
    """
    Returns theoretical maximum line-of-sight between transceivers.

    Parameters
    ----------
    t_h : float
        Transmitter height in meters (m).
    r_h : float
        Receiver height in meters (m).

    Returns
    -------
    float
        Maximum line-of-sight due to Earth curvature in km.

    """
    return (np.sqrt(2*6371000*r_h+r_h**2)/1000)+(np.sqrt(2*6371000*t_h+t_h**2)/1000)

def emission_optical_maximum_distance_with_ducting(t_h,r_h,f_MHz,temp_f,weather_coeff=4/3):
    """
    Returns theoretical maximum line-of-sight between transceivers with ducting consideration.

    Parameters
    ----------
    t_h : float
        Transmitter height in meters (m).
    r_h : float
        Receiver height in meters (m).
    f_MHz : float
        Operating frequency in MHz.
    temp_f : float
        ENV Temperature in fahrenheit.
    weather_coeff : float, optional
        ENV Weather conditions coefficient. The default is 4/3.

    Returns
    -------
    float
        Maximum line-of-sight due to Earth curvature and ducting in km.

    """
    return (np.sqrt(2*weather_coeff*6371000*r_h+temp_f**2)/1000)+(np.sqrt(2*weather_coeff*6371000*t_h+f_MHz**2)/1000)

def get_emission_distance(P_t_watts,f_MHz,G_t,G_r,R_s,t_h,r_h,temp_f,path_loss_coeff=3,weather_coeff=4/3,pure_pathLoss=False):
    """
    Returns theoretical maximum line-of-sight between transceivers all pragmatic consideration.

    Parameters
    ----------
    P_t_watts : float
        Power output of transmitter in watts (W).
    f_MHz : float
        Operating frequency in MHz.
    G_t : float
        Transmitter antenna gain in dBi.
    G_r : float
        Receiver antenna gain in dBi.
    R_s : float
        Receiver sensitivity in dBm *OR* power received in dBm.
    t_h : float
        Transmitter height in meters (m).
    r_h : float
        Receiver height in meters (m).
    temp_f : TYPE
        DESCRIPTION.
    temp_f : float
        ENV Temperature in fahrenheit.
    weather_coeff : float, optional
        ENV Weather conditions coefficient. The default is 4/3.

    Returns
    -------
    float
        Maximum line-of-sight due to path-loss, Earth curvature and ducting in km.

    """
    path_loss = emission_distance(P_t_watts,f_MHz,G_t,G_r,R_s,path_loss_coeff)
    earth_curve = emission_optical_maximum_distance(t_h,r_h)
    earth_curve_with_ducting = emission_optical_maximum_distance_with_ducting(t_h,r_h,f_MHz,temp_f,weather_coeff)
    emissions_distances = [path_loss,earth_curve,earth_curve_with_ducting]
    if pure_pathLoss:
        return path_loss
    else:
        return min(emissions_distances)
    
def get_path_loss_description(path_loss_coeff):
    """
    Return description of RF path-loss situation given a coefficient

    Parameters:
    ----------
    path_loss_coeff : float
        Path-Loss Coefficient, at least 2
    
    Returns:
    ----------
    path_loss_description : str
        Description of RF path-loss situation

    """   
    if path_loss_coeff <= 3:
        path_loss_description = 'Open Terrain'
    elif path_loss_coeff <= 4:
        path_loss_description = 'Moderate Foliage'
    elif path_loss_coeff > 4:
        path_loss_description = 'Dense Foliage'
    return path_loss_description

def create_map(center_coordinate,zs=16,min_z=0,max_z=18):
    """
    Creates a folium basemap for map product development.

    Parameters
    ----------
    center_coordinate : list
        Grid coordinate. Example: [lat,long]
    zs : int, optional
        Initial zoom level [0-18]. The default is 14.
    min_z: int, optional
        Minimum zoom level [0-18]. The default is 0.
    max_z: int, optional
        Maximum zoom level [0-18]. The default is 18

    Returns
    -------
    m : Folium Map Obj
        Folium basemap with satellite tile.

    """
    assert isinstance(center_coordinate,list), 'Coordinate input must be a list.'
    assert len(center_coordinate) == 2, 'Coordinate input must be of length 2.'
    assert min_z <= max_z, 'The max zoom must be greater than the min zoom'
    m = folium.Map(
        location=center_coordinate,
        tiles = None,
        attr = '2ABCT CEMA',
        zoom_start=zs,
        min_zoom = 10,
        max_zoom = 13,
        control_scale = True,
        control_zoom = False,)
    return m

def add_tilelayers(m):
    """
    Adds tilelayers to Folium map object

    Parameters:
    ----------
    m : Folium map object
        Map object
    
    Returns:
    ----------
    m : Folium map object
        Map object

    """
    # folium.TileLayer(
    #     tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    #     attr = 'Esri',
    #     name = 'Satellite',
    #     overlay = False,
    #     control = True,
    #     ).add_to(m)
    folium.TileLayer(
        tiles = 'openstreetmap',
        name = 'Street Map',
        overlay = False,
        control = False,
        min_zoom = 10,
        max_zoom = 13,
        ).add_to(m)
    # folium.TileLayer(
    #     tiles = 'Stamen Toner',
    #     name = 'Black & White',
    #     overlay = False,
    #     control = True
    #     ).add_to(m)
    return m

def add_title(m,df_heatmap=False):
    import datetime
    if df_heatmap:
        min_date = min(list(df_heatmap['Datetime']))
        max_date = max(list(df_heatmap['Datetime']))
    else:
        min_date = max_date = str(datetime.date.today())
    location = 'AL ASAD AIRBASE'
    prefix = '***DEMO***'; suffix = '***DEMO***'
    if min_date == max_date and ':' in min_date:
        map_title = f'{prefix} ELECTROMAGNETIC SPECTRUM (EMS) SURVEY: {location.upper()}, IRAQ at {min_date} {suffix}'
    elif min_date == max_date:
        map_title = f'{prefix} ELECTROMAGNETIC SPECTRUM (EMS) SURVEY: {location.upper()}, IRAQ on {min_date} {suffix}'
    else:
        map_title = f'{prefix} ELECTROMAGNETIC SPECTRUM (EMS) SURVEY: {location.upper()}, IRAQ from {min_date} to {max_date} {suffix}'
    title_html = f'''
                 <h3 align="center" style="font-size:32px;background-color:yellow;color=black;font-family:arial"><b>{map_title}</b></h3>
                 ''' 
    m.get_root().html.add_child(folium.Element(title_html))
    return m

def create_marker(marker_coords,marker_name,marker_color,marker_icon,marker_prefix='fa'):
    marker = folium.Marker(marker_coords,
                  # popup = f'<input type="text" value="{marker_coords[0]}, {marker_coords[1]}" id="myInput"><button onclick="myFunction()">Copy location</button>',
                  popup = f'<input type="text" value="{convert_coords_to_mgrs(marker_coords)}" id="myInput"><button onclick="copyTextFunction()">Copy MGRS Grid</button>',
                  tooltip=marker_name,
                  icon=folium.Icon(color=marker_color,
                                   icon_color='White',
                                   icon=marker_icon,
                                   prefix=marker_prefix)
                  )
    return marker

def create_circle(center_coord,circle_radius_m,circle_color='green',circle_name=None,circle_opacity=1,circle_fill_opacity=0.4,fill_bool=True):
    circle = folium.Circle(
        location=center_coord,
        color=circle_color,
        radius=circle_radius_m,
        fill=fill_bool,
        opacity=circle_opacity,
        fill_opacity=circle_fill_opacity,
        tooltip=circle_name)
    return circle

def add_copiable_markers(m):
    import jinja2
    el = folium.MacroElement().add_to(m)
    el._template = jinja2.Template("""
        {% macro script(this, kwargs) %}
        function copyTextFunction() {
          /* Get the text field */
          var copyText = document.getElementById("myInput");

          /* Select the text field */
          copyText.select();
          copyText.setSelectionRange(0, 99999); /* For mobile devices */

          /* Copy the text inside the text field */
          document.execCommand("copy");
        }
        {% endmacro %}
    """)
    return m

def create_gradient_map(min_value=0,max_value=1,colors=['lightyellow','yellow','orange','red','darkred'],tick_labels = ['None','Poor','Moderate','Good','Excellent'],steps=20):
    assert len(colors) == len(tick_labels), 'Number of colors must equal number of labels'
    index = [min_value,
             np.average([min_value,np.average([min_value,max_value])]),
             np.average([min_value,max_value]),
             np.average([np.average([min_value,max_value]),max_value]),
             max_value]
    assert len(tick_labels) == len(index), 'Index list be equal length number to labels list'
    colormap = cm.LinearColormap(
        colors = colors,
        index = index,
        vmin = int(min_value),
        vmax = int(max_value),
        tick_labels = tick_labels
        )
    gradient_map=defaultdict(dict)
    for i in range(steps):
        gradient_map[1/steps*i] = colormap.rgb_hex_str(min_value + ((max_value-min_value)/steps*i))
    return colormap, gradient_map

def create_polygon(points,line_color='black',shape_fill_color=None,line_weight=5,text=None):
    iframe = folium.IFrame(text, width=250, height=75)
    popup = folium.Popup(iframe, max_width=250)
    polygon = folium.Polygon(locations = points,
                   color=line_color,
                   weight=line_weight,
                   fill_color=shape_fill_color,
                   popup = popup,
                   name = 'test',
                   overlay = False,
                   control = True,
                   show=False
                   )
    return polygon

def organize_polygon_coords(coord_list):
    def clockwiseangle_and_distance(point,origin,refvec):
        import math
        vector = [point[0]-origin[0], point[1]-origin[1]]
        lenvector = math.hypot(vector[0], vector[1])
        if lenvector == 0:
            return -math.pi, 0
        normalized = [vector[0]/lenvector, vector[1]/lenvector]
        dotprod  = normalized[0]*refvec[0] + normalized[1]*refvec[1]
        diffprod = refvec[1]*normalized[0] - refvec[0]*normalized[1]
        angle = math.atan2(diffprod, dotprod)
        if angle < 0:
            return 2*math.pi+angle, lenvector
        return angle, lenvector
    coord_list = sorted(coord_list, key = lambda x: (x[1],x[0]),reverse=True)
    origin = coord_list[0]; refvec = [0,1]
    # ordered_points = coord_list[0]; coord_list = coord_list[1:]
    ordered_points = sorted(coord_list, key = lambda x: clockwiseangle_and_distance(x,origin,refvec))
    return ordered_points
    
def get_line(p1, p2):
    A = (p1[1] - p2[1])
    B = (p2[0] - p1[0])
    C = (p1[0]*p2[1] - p2[0]*p1[1])
    return A, B, -C

def get_intersection(L1, L2):
    D  = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return [x,y]
    else:
        return False

def check_for_intersection(sensor1_coord,end_of_lob1,sensor2_coord,end_of_lob2):
    def ccw(A,B,C):
        return (C[0]-A[0]) * (B[1]-A[1]) > (B[0]-A[0]) * (C[1]-A[1])
    return ccw(sensor1_coord,sensor2_coord,end_of_lob2) != ccw(end_of_lob1,sensor2_coord,end_of_lob2) and ccw(sensor1_coord,end_of_lob1,sensor2_coord) != ccw(sensor1_coord,end_of_lob1,end_of_lob2)
    
def get_polygon_area(shape_coords): # returns area in acres
    x = [convert_coordinates_to_meters(sc[0]) for sc in shape_coords]
    y = [convert_coordinates_to_meters(sc[1]) for sc in shape_coords]    
    return (0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1))))/4046.856422

def get_accuracy_improvement_of_cut(lob1_error,lob2_error,cut_error):
    return 1 - (cut_error/(lob1_error+lob2_error-cut_error))

def get_accuracy_improvement_of_fix(fix_area,cut_areas):
    return 1-(fix_area/(cut_areas[0] + cut_areas[1] + cut_areas[2] - 2*fix_area))

def get_coords_from_LOBs(sensor_coord,azimuth,error,min_lob_length,max_lob_length):
    center_coord_list = []
    right_error_azimuth = (azimuth+error) % 360
    left_error_azimuth = (azimuth-error) % 360
    running_coord_left = [list(sensor_coord)[0],list(sensor_coord)[1]]
    running_coord_center = [list(sensor_coord)[0],list(sensor_coord)[1]]
    running_coord_right = [list(sensor_coord)[0],list(sensor_coord)[1]]
    lob_length = 0
    interval_meters = 30
    while interval_meters > max_lob_length and interval_meters > 10:
        interval_meters -= 10
    near_right_coord = []; near_left_coord = []; far_right_coord = []; far_left_coord = []
    while lob_length <= max_lob_length:
        running_coord_left = adjust_coordinate(running_coord_left,left_error_azimuth,interval_meters)
        running_coord_right = adjust_coordinate(running_coord_right,right_error_azimuth,interval_meters)
        running_coord_center = adjust_coordinate(running_coord_center,azimuth,interval_meters)
        center_coord_list.append(running_coord_center)    
        if lob_length > min_lob_length:
            if near_right_coord == []: near_right_coord = list(running_coord_right)
            if near_left_coord == []: near_left_coord = list(running_coord_left)
        lob_length += interval_meters
    far_right_coord = running_coord_right
    far_left_coord = running_coord_left
    center_coord = get_center_coord([near_right_coord,near_left_coord,far_right_coord,far_left_coord])
    near_center_coord = get_center_coord([near_right_coord,near_left_coord])
    center_coord_list = [c for c in center_coord_list if len(c) <= 2]
    return center_coord, near_right_coord, near_left_coord, near_center_coord, far_right_coord, far_left_coord, running_coord_center, center_coord_list

def get_elevation_data(coord_list):
    import csv, time
    def read_elevation_data(src_file):
        with open(src_file,mode='r',newline='') as elev_data_file:
            csv_reader = csv.reader(elev_data_file)
            csv_data = []
            for row in csv_reader:
                csv_data.append(row)
        return csv_data
    def save_elevation_data(save_file,csv_data):
        with open(save_file,mode='w',newline='') as elev_data_file:
            csv_writer = csv.writer(elev_data_file)
            csv_writer.writerows(csv_data)
    coord_elev_data=[]
    src_file = rf'{os.path.realpath(os.path.dirname(__file__))}\elevation\elev_data.csv'
    cp_file = rf'{os.path.realpath(os.path.dirname(__file__))}\elevation\elev_data_preop_copy.csv'
    if os.path.getsize(src_file) >= os.path.getsize(cp_file):
        shutil.copyfile(src_file, cp_file)
    request_string = ''; request_list = []; request_list_conmprehension = []
    csv_data = read_elevation_data(src_file)
    if len(csv_data) > 1:
        mgrs_list = [d[-2] for d in csv_data[1:]]
        elevation_list = [d[-1] for d in csv_data[1:]]
    else:
        mgrs_list = []; elevation_list = []
    num_coords_in_request = 0; max_request_length = 50; num_stored = 0; num_requested = 0
    for i,coord in enumerate(coord_list):
        mgrs = convert_coords_to_mgrs(coord,precision=4)
        if mgrs in mgrs_list:
            elevation = elevation_list[mgrs_list.index(mgrs)]
            coord_elev_data.append([coord[0],coord[1],mgrs,elevation])
            num_stored += 1
            continue
        else:
            request_list.append(','.join([str(c) for c in coord]))
            num_coords_in_request += 1
            num_requested += 1
        if num_coords_in_request >= max_request_length:
            request_list_conmprehension.append(request_list)
            request_list = []
            num_coords_in_request = 0
            max_request_length = np.random.uniform(48,52)
    if num_requested + num_stored > 0: print(f'{num_stored:,.2f} ({num_stored/(num_requested + num_stored)*100:,.2f}%) tiles already in database')
    if num_requested > num_stored and not check_internet_connection(): return []
    if len(request_list) > 0: request_list_conmprehension.append(request_list)
    if len(request_list_conmprehension) > 0 and len(request_list_conmprehension[0]) > 0:
        for i,requested_coords in enumerate(request_list_conmprehension):
            print(f"Request {i+1} of {len(request_list_conmprehension)}")
            csv_data = read_elevation_data(src_file)
            request_string = '|'.join(requested_coords)
            request = f"https://api.open-elevation.com/api/v1/lookup?locations={request_string}"
            try:
                response = requests.get(request)
                for result in response.json()['results']:
                    latitude = result['latitude']
                    longitude = result['longitude']
                    elevation = result['elevation']
                    mgrs_8digit = convert_coords_to_mgrs([latitude,longitude],precision=4)
                    coord_elev_data.append([latitude,longitude,mgrs_8digit,elevation])
                    csv_data.append([latitude,longitude,mgrs_8digit,elevation])
                print(f'Success: {len(requested_coords)} datapoints added to elevation database')
            except:
                print(f"Elevation request {i+1} failed.")
            save_elevation_data(src_file,csv_data)
            time.sleep(np.random.exponential(0.125))
    return coord_elev_data

def plot_elevation_data(coord_elev_data,target_coords=None,title_args=None):
    import datetime
    if coord_elev_data == None or len(coord_elev_data) == 0: return 0
    def get_dist_interval(target_distance,dist_interval):
        if target_distance is None: return -1
        for i, di in enumerate(dist_interval[:-1]):
            if int(di) <= target_distance < int(dist_interval[i+1]):
                return i
        return -1
    # input maybe title?, maybe filename?
    import matplotlib.pyplot as plt
    elev_list = [float(x[-1]) for x in coord_elev_data]
    base_reg=0
    sensor_coord = [coord_elev_data[0][0],coord_elev_data[0][1]]
    sensor_mgrs = convert_coords_to_mgrs(sensor_coord)
    far_side_coord = [coord_elev_data[-1][0],coord_elev_data[-1][1]]
    far_side_coord_mgrs = convert_coords_to_mgrs(far_side_coord)
    distance = int(get_distance_between_coords(sensor_coord,far_side_coord))
    coord_interval = int(distance/len(elev_list))
    dist_interval = list(range(0,distance,coord_interval))
    target_dist_indices = []
    if target_coords is not None:
        for i,target_coord in enumerate(target_coords):
            if i == len(target_coords)-1: target_dist_indices.append(-1); break
            target_dist = get_distance_between_coords(sensor_coord,target_coord)
            target_dist_index = get_dist_interval(target_dist,dist_interval)
            target_dist_indices.append(target_dist_index)
    while len(dist_interval) > len(elev_list):
        dist_interval = dist_interval[:-1]
    while len(dist_interval) < len(elev_list):
        dist_interval = dist_interval + [dist_interval[-1]+coord_interval]
    try:   
        plt.figure(figsize=(10,4))
        # plt.style.use('ggplot')
        plt.style.use('classic')
        plt.plot(dist_interval,elev_list)
        min_elev = min(elev_list)
        max_elev = max(elev_list)
        plt.plot([0,dist_interval[-1]],[min_elev,min_elev],'--g',label='min: '+str(min_elev)+' m')
        plt.plot([0,dist_interval[-1]],[max_elev,max_elev],'--r',label='max: '+str(max_elev)+' m')
        # plt.scatter([0],[elev_list[0]],label='Sensor',color='blue',marker='^',s=100)
        buffer = int(min_elev *.25)
        plt.ylim(int(min_elev - buffer), int(max_elev + buffer))
        plt.xlim(dist_interval[0],dist_interval[-1])
        if target_coords is not None:
            target_dists = []; target_elevations = []
            for i,target_coord in enumerate(target_coords):
                if i == len(target_coords)-1: target_dists.append(dist_interval[-1]); target_elevations.append(elev_list[-1]); break
                target_dist = get_distance_between_coords(sensor_coord,target_coord)
                target_dists.append(target_dist)
                target_elevations.append(elev_list[target_dist_indices[i]])
            plt.vlines(target_dists,[min_elev - buffer for td in target_dists],[max_elev + buffer for td in target_dists],colors=['black' for dt in target_dists],linestyles=['dashed' for dt in target_dists],label='Target Distances')
            plt.scatter(target_dists,target_elevations,label='Possible Targets',color='red',marker='D',s=100)
        plt.fill_between(dist_interval,elev_list,base_reg,alpha=0.1,color='green')
        plt.xlabel("Distance (m)")
        plt.ylabel("Elevation (m)")
        plt.grid()
        plt.legend(fontsize='small')
        if title_args is None:
            plt.title(f'Elevation data from {sensor_mgrs} to {far_side_coord_mgrs}')
        else:
            if len(title_args) == 1:
                plt.title(f'Elevation data from {title_args[0]} to {far_side_coord_mgrs}')
            elif len(title_args) == 2:
                plt.title(f'Elevation data from {title_args[0]} to {title_args[1]}')
        dt = str(datetime.datetime.today()).split()[0].replace('-','')
        num = 0
        output_filename = (rf'{os.path.realpath(os.path.dirname(__file__))}\elevation_plots\{dt}_elevation_data_{num:02}.png')
        while os.path.exists(output_filename):
            num +=1 
            output_filename = (rf'{os.path.realpath(os.path.dirname(__file__))}\elevation_plots\{dt}_elevation_data_{num:02}.png')
        plt.savefig(output_filename)
        plt.show()
    except AttributeError as e:
        return 0
    
def get_fix_coords(points_cut_polygons):
    def get_polygon(points):
        try:
            p1, p2, p3, p4 = map(Point, points)
            poly = Polygon(p1, p2, p3, p4)
        except ValueError:
            p1, p2, p3 = map(Point, points)
            poly = Polygon(p1, p2, p3)
        return poly
    def get_intersection_coords(intersection):
        x_coords = []; y_coords = []
        for index,ip in enumerate(intersection):
            try:
                x = round(float(intersection[index].x),13)
                y = round(float(intersection[index].y),13)
                if x not in x_coords and y not in y_coords:
                    x_coords.append(x)
                    y_coords.append(y)
                    # print("x:",x); print("y:",y)
            except AttributeError:
                x1 = float(intersection[index].p1.x)
                y1 = float(intersection[index].p1.y)
                if x1 not in x_coords and y1 not in y_coords:
                    x_coords.append(x1)
                    y_coords.append(y1)
                    # print("x1:",x); print("y1:",y)
                x2 = float(intersection[index].p2.x)
                y2 = float(intersection[index].p2.y)
                if x2 not in x_coords and y2 not in y_coords:
                    x_coords.append(x2)
                    y_coords.append(y2)
                    # print("x2:",x); print("y2:",y)
        coords = [[x,y_coords[i]] for i,x in enumerate(x_coords)]
        return coords
    poly1 = get_polygon(points_cut_polygons[0])
    poly2 = get_polygon(points_cut_polygons[1])
    poly3 = get_polygon(points_cut_polygons[2])
    intersection_1_2 = poly1.intersection(poly2)
    intersection_1_3 = poly1.intersection(poly3)
    coords_intersection_1_2 = get_intersection_coords(intersection_1_2)
    coords_intersection_1_3 = get_intersection_coords(intersection_1_3)
    int_poly1 = get_polygon(coords_intersection_1_2)
    int_poly2 = get_polygon(coords_intersection_1_3)
    fix_intersection = int_poly1.intersection(int_poly2)
    fix_coords = get_intersection_coords(fix_intersection)
    return fix_coords

def create_line(points,line_color='black',line_weight=5,line_popup=None,dash_weight=None):
    line = folium.PolyLine(locations = points,
                    color = line_color,
                    weight = line_weight,
                    dash_array = dash_weight,
                    tooltip = line_popup
                    )
    return line

def plot_LOB(points_lob_polygon,azimuth,sensor_error,min_distance_m,max_distance_m):
    lob_description = f'{azimuth}° with {sensor_error}° RMS error from {min_distance_m/1000:.1f} to {max_distance_m/1000:.1f}km ({get_polygon_area(points_lob_polygon):,.0f} acres of error)'
    lob_polygon = create_polygon(points_lob_polygon,'black','blue',2,lob_description)
    return lob_polygon

def create_lob_cluster(lob_cluster,points_lob_polygons,azimuths,sensor_error,min_distance_m,max_distance_m):
    for index,plp in enumerate(points_lob_polygons):
        lob_polygon = plot_LOB(plp,azimuths[index],sensor_error,min_distance_m,max_distance_m)
        lob_cluster.add_child(lob_polygon)
    return lob_cluster

def plot_grid_lines(center_coord,num_gridlines = 10,precision = 5, adj_increment_m = 1000):
    def round_to_nearest_km(num):
        km = str(round(int(num)*10**(-1*(len(num)-2)),0)).replace('.','')
        if num[0] == '0' and len(km) < 5: km = '0' + km
        while len(km) < len(num):
            km += '0'
        return km
    def round_coord_to_nearest_mgrs_km2(center_coord,precision=5):
        center_coord_preamble = convert_coords_to_mgrs(center_coord,precision)[:precision*-2]
        easting = convert_coords_to_mgrs(center_coord,precision)[precision*-2:precision*-1]
        northing = convert_coords_to_mgrs(center_coord,precision)[precision*-1:]
        return center_coord_preamble+round_to_nearest_km(easting)+round_to_nearest_km(northing)
    def adjust_mgrs(starting_mgrs,direction,distance_m):
        starting_coord = convert_mgrs_to_coords(starting_mgrs)
        if direction == 'e':
            azimuth = 90
        elif direction == 'w':
            azimuth = 270
        elif direction == 'n':
            azimuth = 0
        elif direction == 's':
            azimuth = 180
        try:
            raise
        except:
            coord = adjust_coordinate(starting_coord,azimuth,distance_m)
            mgrs = round_coord_to_nearest_mgrs_km2(coord)
            if mgrs == starting_mgrs:
                new_mgrs = convert_coords_to_mgrs(coord)
                adjust_mgrs(new_mgrs,direction,distance_m)
        return mgrs, coord
    def incremental_points(starting_mgrs,orientation,increment_vector,num_increments):
        running_mgrs = starting_mgrs
        running_coord= convert_mgrs_to_coords(starting_mgrs)      
        point_list = [(running_coord,running_mgrs)]           
        for i in range(num_increments):
            # distance = (i+1)*increment_vector
            running_mgrs, running_coord = adjust_mgrs(running_mgrs,orientation,increment_vector)
            point_list.append((running_coord,running_mgrs))
        return point_list
    def realign_points(item_list):
        new_list = []
        mgrs_list = []
        for item in item_list:
            mgrs = round_coord_to_nearest_mgrs_km2(item[0])
            if mgrs in mgrs_list:
                continue
            coord = convert_mgrs_to_coords(mgrs)
            mgrs_list.append(mgrs)
            new_list.append((coord,mgrs))
        return new_list
    center_mgrs = round_coord_to_nearest_mgrs_km2(center_coord)
    center_coord = convert_mgrs_to_coords(center_mgrs)
    base_points_hl = [(center_coord,center_mgrs)]
    base_points_vl = [(center_coord,center_mgrs)]
    base_points_hl = incremental_points(center_mgrs,'e',adj_increment_m,num_gridlines)+incremental_points(center_mgrs,'w',adj_increment_m,num_gridlines)
    base_points_vl = incremental_points(center_mgrs,'n',adj_increment_m,num_gridlines)+incremental_points(center_mgrs,'s',adj_increment_m,num_gridlines)    
    base_points_hl = sorted(base_points_hl,key = lambda x: x[0][1])
    base_points_vl = sorted(base_points_vl,key = lambda x: x[0][0])
    east_center_mgrs = base_points_hl[-1][1]
    west_center_mgrs = base_points_hl[0][1]
    north_center_mgrs = base_points_vl[-1][1]
    south_center_mgrs = base_points_vl[0][1]
    e_boundary_points = incremental_points(east_center_mgrs,'n',adj_increment_m,num_gridlines)+incremental_points(east_center_mgrs,'s',adj_increment_m,num_gridlines)
    e_boundary_points = sorted(e_boundary_points,key = lambda x: x[0][0])
    w_boundary_points = incremental_points(west_center_mgrs,'n',adj_increment_m,num_gridlines)+incremental_points(west_center_mgrs,'s',adj_increment_m,num_gridlines)
    w_boundary_points = sorted(w_boundary_points,key = lambda x: x[0][0])
    s_boundary_points = incremental_points(south_center_mgrs,'e',adj_increment_m,num_gridlines)+incremental_points(south_center_mgrs,'w',adj_increment_m,num_gridlines)
    s_boundary_points = sorted(s_boundary_points,key = lambda x: x[0][1])
    n_boundary_points = incremental_points(north_center_mgrs,'e',adj_increment_m,num_gridlines)+incremental_points(north_center_mgrs,'w',adj_increment_m,num_gridlines)
    n_boundary_points = sorted(n_boundary_points,key = lambda x: x[0][1])
    n_boundary_points = realign_points(n_boundary_points)
    s_boundary_points = realign_points(s_boundary_points)
    w_boundary_points = realign_points(w_boundary_points)
    e_boundary_points = realign_points(e_boundary_points)
    lines = []
    previous_nbp = []
    for sbp in s_boundary_points:
        easting = sbp[1][precision*-2:precision*-1]
        best_lon_diff = np.inf
        opposite_north_coord = ''
        for nbp in n_boundary_points:
            lon_diff = abs(sbp[0][1] - nbp[0][1])
            if lon_diff < best_lon_diff and nbp[0] not in previous_nbp:
                best_lon_diff = lon_diff
                opposite_north_coord = nbp[0]
        previous_nbp.append(opposite_north_coord)    
        line = create_line([sbp[0],opposite_north_coord],'black',2,f'Easting: {easting}')
        lines.append(line)
    previous_wbp = []
    for ebp in e_boundary_points:
        northing = ebp[1][precision*-1:]
        best_lat_diff = np.inf
        opposite_west_coord = ''
        for wbp in w_boundary_points:
            lat_diff = abs(ebp[0][0] - wbp[0][0])
            if lat_diff < best_lat_diff and wbp[0] not in previous_wbp:
                best_lat_diff = lat_diff
                opposite_west_coord = wbp[0]
        previous_wbp.append(opposite_west_coord)
        line = create_line([ebp[0],opposite_west_coord],'black',2,f'Northing: {northing}')
        lines.append(line)               
    return lines


## TEST ###
if __name__ == '__main__':
    import os
    from folium.plugins import MarkerCluster
    center_coord = [51.62788019542925, 15.274024744828047]
    adjusted_coord = adjust_coordinate(center_coord,azimuth_degrees=160,shift_m=2000)
    print(adjusted_coord)
    print(convert_coords_to_mgrs(adjusted_coord))

    '''https://api.open-elevation.com/api/v1/lookup?locations=51.24885624303748,15.570668663974097'''





