Deforestation alert analysis
============================

.. note::

    This documentation is not complete, work in progress.
    
.. warning::

    To use this module, one must have least register to the NICFI planetLab programm and link it's GEE account to it. More information can be found in `Register to NICFI programm<https://docs.sepal.io/en/latest/setup/nicfi.html>`__.


Set up
------

From the SEPAL app dashboard (purple :icon:`fas fa-wrench` on the left side), search for and click on **deforestation alert analysis**.

The application should launch itself in the :icon:`fas fa-map` section. On the left side the navdrawer will help you navigate between the different pages of the app. If you click on :btn:`<fas fa-book-open> wiki`, :btn:`<fas fa-bug> bug report` or :btn:`<fas fa-file-code> code source`, you will be redirected to the corresponding webpage.

.. note::

    The launching process can take several minutes

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/landing.png 
    :title: the interface displayed to the end user
    :group: alert-module
    
To improve the display of the tool click on the :btn:`<fas fa-expand>` icon in the top left corner of the map. It will change the display to fullscreen. From here everything can be done using the widgets. 

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/fullscreen.png 
    :title: the interface displayed in fullscreen.
    :group: alert-module
    
On the top left corner of the map. 3 buttons will help the user navigate through the different widgets of the application:

-   :btn:`<fas fa-bars>`: the setting of the alerts displayed on the map
-   :btn:`<fas fa-globe>`: the Planet interface to navigate through the different available images
-   :btn:`<fas fa-info>`: the metadata panel where the user can set evaluate the alerts


.. tip::

    By design this different panels will open and close when needed. If it's not the case you can close them by clicking on the :icon:`fas fa-times` and toggle them by clicking on their respective button.
    
Settings
--------

The settings need to be fully validated to load the alerts on the map. it has 3 sections **AOI**, **Planet** and ** It's de first step of the process.

Area of interest
^^^^^^^^^^^^^^^^

The area o interest, also called AOI is set using the same AOI interface as in other applications. You can read the `module aoi <https://docs.sepal.io/en/latest/feature/aoi_selector.html#module-aoi>`__ for more information. 

In this step the user will be able to select any type of AOI method. when validated, the AOI will be displayed in gold on the map. 

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/aoi.png 
    :title: The selection of an AOI.
    :group: alert-module

Planet
^^^^^^

.. note::

    this panel is fully optional. If nothing is set, The module will use Planet NICFI level 1 data (monthly mosaics). If you have a NICFI level 2 access, providing your API key will grant you access to daily imagery.

click on **Planet** to access the second tab and fill the Planet API key field withthe one associated your NICFI level 2 programm. once validated you'll be able to modify the Planet advance parameters. This parameters are use to request images to Planet, some default parameter have been set but changing may improve the readability of the image. 

-   **number of images**: the max number of images to display on the map, default to 6
-   **day before**: number of previous day the interface can search for images. useful when lot of cloud coverage, default to 1 
-   **day after**: number of previous day the interface can search for images. useful when lot of cloud coverage, default to 1
-   **cloud coverage**: the requested maximal cloud coverage of the images, default to 20%

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/planet_settings.png 
    :title: The planet settings
    :group: alert-module

Alerts
^^^^^^

The user then need to select the alert system to use. various drivers are available in the module and the documentation will reflects any changes or addition made by the SEPAL team.

The process is simple, select a driver in the dropdown list, then select a date range. It can be xx days in the past using the "recent" mode or any time in the past using the "historical" mode. using the slider, the ser can filter the minimal size of the alerts from 0 to 100 ha. 0 corresponding to no filter at all.

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/glad_l_settings.png 
    :width: 24%
    :title: when selecting The GLAD-L widget
    :group: alert-module
    
.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/radd_settings.png 
    :width: 24%
    :title: when selecting The RADD widget
    :group: alert-module
    
.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/nrt_settings.png 
    :width: 24%
    :title: when selecting The NRT widget
    :group: alert-module
    
.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/glad_s_settings.png 
    :width: 24%
    :title: when selecting The GLAD-S widget
    :group: alert-module

GLAD-L
######

.. warning::

    The GLAD-L repository is currently under heavy maintenance, no alerts from 2022 are available. only historical date from 2018 to 2021 can be selected. more information `here <https://code.earthengine.google.com/4c46540499ee0f7b7c14959a069927d2>`__.

Selecting this alert system, the user will use the GLAD alerts based on the lansdsat satellites.

    Since the opening of the Landsat archive in 2008, medium spatial resolution data have been available for use in alert-based applications.  Since 2013, two Landsat sensors, the Enhanced Thematic Mapper Plus (ETM+) onboard Landsat 7, and the Operational Land Imager (OLI) onboard Landsat 8, have been systematically acquiring global multi-spectral observations at a 30m spatial resolution.  The orbits of the two spacecraft are coordinated to enable potential 8-day repeat coverage globally.   Given this cadence, the use of Landsat as a near-real time source of land change information is possible. The data displayed and made available here quantify forest disturbance events for the tropics using ETM+ and OLI data as an input.  Daily updates are made for areas where quality land observations are acquired.  We define forest cover as 5m tall trees with a canopy closure exceeding 30%.  An alert is defined as any Landsat pixel that experiences a canopy loss in excess of 50% cover.
    
More information on these alerts can be found on the `GLAD forest alert page <https://glad.umd.edu/dataset/glad-forest-alerts>`__.

RADD
####

.. info::

    RADD alerts only covers the tropical part of the Americas and Africa. More information can be found in their documenation.
    
Selecting this alert system, the user will use the RADD alerts: 

    Sentinel-1’s cloud-penetrating radar provides gap-free observations for the tropics consistently every 6 to 12 days. In the densely cloud covered tropics, this represents a major advantage for the rapid detection of small-scale forest disturbances such as subsistence agriculture and selective logging. The RADD (RAdar for Detecting Deforestation) alerts contribute to the World Resources Institute’s Global Forest Watch initiative in providing timely and accurate information to support a wide range of stakeholders in sustainable forest management and law enforcement activities against illegal deforestation. The RADD alerts are implemented in Google Earth Engine. RADD alerts are available openly via Google Earth Engine, the Global Forest Watch platform, SEPAL.io and EarthMap.org.
    
More information on these alerts caan be found on the `Wageningen university portal <https://www.wur.nl/en/Research-Results/Chair-groups/Environmental-Sciences/Laboratory-of-Geo-information-Science-and-Remote-Sensing/Research/Sensing-measuring/RADD-Forest-Disturbance-Alert.htm>`__.

NRT
###

.. danger::

    This fonctionality will remain experimental until the SEPAL team provide support for the creation of near real time alert assets through a cookbook recipe. 
    
Selecting this alert system, the user will use the near real time alert system provided by the SEPAL team. 
here instead of providing dates, the user only needs to provide access to the alert asset produced by the recipe.

GLAD-S
######

.. warning::

    When publishing this documentation (2022-04-26) only the north part of south alerica is covered by the alert system. open the following `link <https://code.earthengine.google.com/3b5238d7558dbafec5072838f1bac1e9?hideCode=true>`__ to see the area in the GEE code editor. 
    
Selecting this alert system, the user will use the GLAD alerts based on the Sentinel 2 satellites.

    Loss of primary forest is mapped in near-real time at 10m resolution using Sentinel-2 multispectral data. Cloud, shadow, water are detected in each new Sentinel-2 image and a forest loss algorithm is applied to all remaining clear land observations. The algorithm relies on the spectral data in each new image in combination with spectral metrics from a baseline period of the previous two years. Confidence is built through repeated loss observations in the consequent images. 

Once everything is set, the user can click on :btn:`select alerts` and the module will start downloading the information from google earth engine. the module will tile the AOI in smaller chunks to avoid GEE limitation, if you use a big area downloading can take up to 15 min. The alerts are displayed as shapes in red on the map and the settings panel will close automatically. If alerts are found in your AOI, the metadata panel will open automatically.

Metadata
--------

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/metadata.png 
    :title: the metadata of the alerts
    :group: alert-module

The metadata panel will allow the user to validate the displayed alerts. on the top you'll fint the list of alerts ordered by size. to acess them the user can either click on the blue arrows or click on the carret to select one in the dropdown menu. Once an alert is selected (represented now in orange on the map), the Planet panel will open itself on the top right corner of the map and the information of the alert will be displayed. Change the value of the radio "review" from:

- :code:`yes`: the alert is valid as well as the date
- :code:`no`: the alert is not valid
- :code:`unset`: no review has been performed

.. tip::

    TO move from one alert to another, the user can also directly click on the map, the information will be loaded automatically.

To evaluate the validity of the alert the user can use the available Planet imagery.

Planet
------

This module provide easy access to NICFI Planet imagery to help validating the alerts. based on the filled API key, level 1 or level 2 data will be used. 

Level 1 (monthly)
^^^^^^^^^^^^^^^^^

Level 1 data are monthly mosaics. when a alert is clicked, the module will load the closest month from the observation date. the user can then use the Planet navigator to change the displayed image. 
Click on the :btn:`<fas fa-palette>` to change the color of the images from CIR to RGB. The user can select the monthly mosaic directly from the dropdown menu or use the navigation buttons. :btn:`<fas fa-chevron-left>` (res. :btn:`<fas fa-chevron-right>`) will move from one mont in the past (res. in the future). The :btn:`<fas fa-circle>` will set back on the closest date from the observation date. 

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/planet_monthly_rgb.png 
    :width: 49%
    :title: the planet monthly mosaic displayed in rgb
    :group: alert-module

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/planet_monthly_cir.png 
    :title: the planet monthly mosaic displayed in cir
    :group: alert-module
    
Level 2 (daily)
^^^^^^^^^^^^^^^

.. warning::

    This option is only available for users that have a NICFI level 2 access.
    
Level 2 data are daily imagery. When an alert is clicked, the module will load the closest day from the observation date and display images using the advanced parameters provided by the user. 

.. tip::

    Multiple images are displayed at once so don't hesitate to play with the layer control to hide and show different scenes.
    
Thus user can navigate through the images using the buttons in the Planet navigator. Click on :btn:`<fas fa-chevron-left>` (res. :btn:`<fas fa-chevron-right>`) to move one day in the past (res. one day in the future). Click on :btn:`<fas fa-chevrons-left>` (res. :btn:`<fas fa-chevrons-right>`) to move one month in the past (res. one month in the future). The :btn:`<fas fa-circle>` will set back on the closest date from the observation date. 

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/planet_daily.png 
    :title: the planet daily mosaic displayed in cir
    :group: alert-module
    
Export
------

Once the alerts are validated, the user can download them in .csv using the center of the alert as coordinates or as a geopackage (.gpkg) to keep the shapes of the alerts. 

.. thumbnail:: https://raw.githubusercontent.com/sepal-contrib/alert_module/master/doc/img/validate_download.png 
    :title: the planet daily mosaic displayed in cir
    :group: alert-module

    





    






    
