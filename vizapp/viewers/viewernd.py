import logging

import numpy as np
import plotly.graph_objs as go
from ipywidgets import IntSlider, Dropdown, HBox, VBox, Label, FloatText, Button, IntText

from .viewer import Viewer

logging.basicConfig(filename='/tmp/vizapp.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
logger = logging.getLogger('viewernd')

class ViewerND(Viewer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._thedata = self._vizapp.get_data(0)

        self._theoverlay = None

        # Slice slider
        self._slice_slider = IntSlider(description='Slice #:', max=10)
        self._slice_slider.observe(self._slice_slider_on_value_change)

        # TODO: refactor this
        self._slice_slider.max = self._thedata.shape[0]

        # Data selector
        self._data_dropdown = Dropdown(description='Data:', options=self._vizapp._3d_data.keys())
        self._data_dropdown.observe(self._data_dropdown_on_change)

        # Overlay selector
        self._overlay_dropdown = Dropdown(description='Overlay:', options=['None'] + list(self._vizapp._2d_data.keys()))
        self._overlay_dropdown.observe(self._overlay_dropdown_on_change)

        # Processing selector
        self._processing_dropdown = Dropdown(description='Processing:', options=['Select...'] + list(self._vizapp.get_3d_processing()))
        self._processing_dropdown.observe(self._processing_dropdown_on_change)
        self._processing_vbox = VBox([])

        self._show_image()

        self._fig = go.FigureWidget(self._gofig)

        self._line1 = HBox([self._data_dropdown, self._overlay_dropdown])


    def _data_dropdown_on_change(self, change):
        """
        Callback: Data dropdown change.

        Parameters
        ----------
        change : dict
            Change information from ipywidgets

        Returns
        -------

        """
        if change['type'] == 'change' and change['name'] == 'value':
            self._thedata = self._vizapp.get_data(change['new'])

            # Set the slice slider maximum
            self._slice_slider.max = self._thedata.shape[0]

            if self._current_slice > self._thedata.shape[0] - 1:
                self._current_slice = self._thedata.shape[0] - 1

            # Get the data and update the figure
            self._update_image()

    def _overlay_dropdown_on_change(self, change):
        """
        Callback: 2D overlay call back change.

        Parameters
        ----------
        change : dict
            Change information from ipywidgets

        Returns
        -------

        """

        logger.debug('overlay_dropdown_on_change with change {}'.format(change))
        if change['type'] == 'change' and change['name'] == 'value':
            self._theoverlay = self._vizapp.get_data(change['new'])

            logger.debug('\tgoing to call update image')
            self._update_image()

    def _processing_dropdown_on_change(self, change):
        """
        Here we want to put the parameters and some buttons in the right hand
        self._processing_vbox.
        """

        if change['type'] == 'change' and change['name'] == 'value':

            if change['new'].startswith('Select'):
                self._processing_vbox.children = ()
            else:
                self._build_procesing_panel(self._vizapp.get_3d_processing(change['new']))

    def _build_procesing_panel(self, processing_info):
        """
        Build up the processing panel for filtering data.

        Parameters
        ----------
        processing_info: dict
            Processing information that contains name and parameters.

        Returns
        -------

        """
        self._processing_parameters = processing_info

        parameter_list = []

        # Add the title to the top of the processing area.
        title = Label('Process: ' + processing_info['name'], style={'font-weight': 'bold', 'font-size': '1.5em'})
        title.layout.width = '100%'

        parameter_list.append(title)

        # Add all the parameters
        for parameter in self._processing_parameters.get('parameters'):
            if isinstance(parameter[1], (int, float)):

                label = Label(parameter[0])
                label.layout.width = '50%'

                if isinstance(parameter[1], int):
                    ft = IntText(value=parameter[1])
                elif isinstance(parameter[1], float):
                    ft = FloatText(value=parameter[1])
                ft.layout.width = '50%'

                box = HBox((label, ft ))
                parameter_list.append(box)

        # Add the Cancel and Process buttons
        cancel_button = Button(description='Cancel', value='Cancel')
        cancel_button.button_style = 'danger'
        cancel_button.on_click(self._processing_cancel_button_callback)

        process_button = Button(description='Process', value='Process')
        process_button.button_style = 'success'
        process_button.on_click(self._processing_process_button_callback)

        parameter_list.append(HBox((process_button, cancel_button)))

        # Add them all to the VBox
        self._processing_vbox.children = tuple(parameter_list)

    def _processing_cancel_button_callback(self, *args, **kwargs):
        self._processing_vbox.children = ()

    def _processing_process_button_callback(self, *args, **kwargs):
        logger.debug('-------------------')
        logger.debug(*args)

        # Get the data
        data_name = self._data_dropdown.value
        data = self._vizapp.get_data(data_name)

        # Get the function
        function = self._processing_parameters['method']

        # Need to see which parameters need to be passed to the function
        params = {
            self._processing_parameters['data_parameter']: data
        }
        for ii, row in enumerate(self._processing_vbox.children):
            logger.debug('{}th row is {}'.format(ii, row))
            if hasattr(row, 'children') and len(row.children) == 2 and isinstance(row.children[1], FloatText):
                label, box = row.children
                logger.debug('label is {}'.format(label))
                logger.debug('box is {}'.format(box))
                params[label.value] = box.value
            elif hasattr(row, 'children') and len(row.children) == 2 and isinstance(row.children[1], IntText):
                label, box = row.children
                logger.debug('label is {}'.format(label))
                logger.debug('box is {}'.format(box))
                params[label.value] = box.value

        logger.debug('Got parameters {}'.format(params))


        logger.debug('_processing_process_button_callback: going to call {} with {}'.format(
            function,
            params
        ))
        new_data = function(**params)

        logger.debug('Data returned from {} with params {} is {}'.format(function, params, new_data))

        # Add the new data to vizapp
        self._vizapp.add_data(data_name + '-' + self._processing_parameters['name'], new_data)

        # Reset the GUI
        self._processing_dropdown.index=0
        self._processing_vbox.children = ()

        self._data_dropdown.options = self._vizapp._3d_data.keys()
        self._overlay_dropdown.options = ['None'] + list(self._vizapp._2d_data.keys())

    def _slice_slider_on_value_change(self, change):
        """
        Callback: Slice Slider change

        Parameters
        ----------
        change: dict
            Dictionary of change information from an ipywidgets item.

        Returns
        -------

        """

        # Get the new value and make sure we are looking only for change
        # in value
        try:
            if change.get('type', '') == 'change' and change.get('name', '') == 'value':
                sl = change['new']

                # If current, stop, else update
                if sl == self._current_slice:
                    return
                else:
                    self._current_slice = sl

                self._update_image()

        except Exception as e:
            print(change)

    def _show_image(self):
        raise NotImplementedError('Must be implemented in a sub-class')

    def _update_image(self):
        raise NotImplementedError('Must be implemented in a sub-class')

    def show(self):
        display(
            HBox([
                VBox([
                    self._line1,
                    self._fig,
                    HBox([self._slice_slider, self._processing_dropdown])
                ]),

                # Add in the vertical thing on the right for processing parameters
                self._processing_vbox
            ])
        )

class PlotlyViewerND(ViewerND):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _update_image(self):
        td = self._thedata[self._current_slice]
        self._fig.data[0].update({'z': td})

        if not self._overlay_dropdown.value == 'None':
            self._fig.data[1].update({
                "x": np.arange(74),
                "y": np.arange(74),
                "z": self._theoverlay,
                "opacity": 0.5,
                "showlegend": False,
                "type": "heatmap"
            })
        else:
            self._fig.data[1].update({
                "x": [0],
                "y": [0],
                "z": [0],
                "opacity": 1,
                "showlegend": False,
                "type": "heatmap"
            })

    def _show_image(self):

        self._current_slice = 0

        colorscale = [(x, 'rgb({}, {}, {})'.format(int(x*255), int(x*255), int(x*255))) for x in np.arange(0, 1, 0.1)]

        self._trace1 = {
            "name": "data",
            "x": np.arange(74),
            "y": np.arange(74),
            "z": self._thedata[0],
            "colorscale": colorscale,
            "showlegend": False,
            "type": "heatmap"
        }

        data2show = [self._trace1]

        # logger.debug('Going to show with overlay {}'.format(self._overlay_dropdown.value))
        # if not self._overlay_dropdown.value == 'None':
        #     name = self._overlay_dropdown.value
        #     data = self._vizapp._2d_data[name]
        #
        overlay_data = {
            "name": "overlay",
            "x": [0],
            "y": [0],
            "z": [0],
            "opacity": 1,
            "colorscale": colorscale,
            "showlegend": False,
            "type": "heatmap"
        }

        data2show += [overlay_data]

        self._data = go.Data(data2show)

        layout = {
            "legend": {
                "x": 1,
                "y": 0.5,
                "bgcolor": "rgb(255,255,255)"
            },
            "margin": {"r": 10},
            "paper_bgcolor": "rgb(255,255,255)",
            "plot_bgcolor": "rgb(229,229,229)",
            "width": 500,
            "height": 500,
            "showlegend": True,
            "xaxis": {
                "gridcolor": "rgb(255,255,255)",
                "showgrid": True,
                "showline": False,
                "showticklabels": True,
                "tickcolor": "rgb(127,127,127)",
                "ticks": "outside",
                "title": "x",
                "type": "linear",
                "zeroline": False
            },
            "yaxis": {
                "gridcolor": "rgb(255,255,255)",
                "showgrid": True,
                "showline": False,
                "showticklabels": True,
                "tickcolor": "rgb(127,127,127)",
                "ticks": "outside",
                "title": "y",
                "type": "linear",
                "zeroline": False
            }
        }

        self._gofig = go.Figure(data=self._data, layout=layout)
