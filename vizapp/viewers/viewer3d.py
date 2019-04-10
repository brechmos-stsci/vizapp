import numpy as np
import plotly.graph_objs as go
from ipywidgets import IntSlider, Dropdown, HBox, VBox, Label, FloatText, Button


class Viewer:

    def __init__(self, vizapp):

        self._vizapp = vizapp


class Viewer1D(Viewer):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


class Viewer2D(Viewer):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)


class Viewer3D(Viewer):

    def __init__(self, *args, **kwargs):

        """
        Viewer3D is a layer that defines the data dropdown, overlay dropdown
        and some other things. It would be sub-classed in order to define the
        method of actually displaying.
        """
        super().__init__(*args, **kwargs)

        # Slice slider needs to be defined along with self._slice_slider_on_value_change
        self._slice_slider = None

        # Data selector needs to be defined along with self._data_dropdown_on_change
        self._data_dropdown = None

        # Overlay selector needs to be defined along with self._data_overlay_on_change
        self._overlay_dropdown = None

    #
    # Call backs
    #

    def _data_dropdown_on_change(self, change):
        """
        Change of data selector.
        """
        raise NotImplementedError('Must implement in a sub-class')


    def _overlay_dropdown_on_change(self, change):
        """
        Change of overlay selector.
        """
        raise NotImplementedError('Must implement in a sub-class')

    def _slice_slider_on_value_change(self, change):
        """
        Call back for int slider call back
        """
        raise NotImplementedError('Must implement in a sub-class')

    def _show_image(self):
        raise NotImplementedError('Must implement in a sub-class')


class PlotlyViewer3D(Viewer3D):

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
            td = self._thedata[self._current_slice]
            self._fig.data[0].update({'z': td})

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

        if change['type'] == 'change' and change['name'] == 'value':
            self._theoverlay = self._vizapp.get_data(change['new'])

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
            if isinstance(parameter[1], float):

                label = Label(parameter[0])
                label.layout.width = '50%'

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

        # Get the data
        data_name = self._data_dropdown.value
        data = self._vizapp.get_data(data_name)

        new_data = self._processing_parameters['method'](data,
                                                         self._processing_parameters['parameters'][1][1])

        self._vizapp.add_data(data_name + '-' + self._processing_parameters['name'], new_data)

        # Reset the GUI
        self._processing_dropdown.index=0
        self._processing_vbox.children = ()

        self._data_dropdown.options = self._vizapp._3d_data.keys()



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

                # Get the data and update the figure
                td = self._thedata[sl]
                self._fig.data[0].update({'z': td})

        except Exception as e:
            print(change)

    def _show_image(self):

        self._current_slice = 0

        colorscale = [(x, 'rgb({}, {}, {})'.format(int(x*255), int(x*255), int(x*255))) for x in np.arange(0, 1, 0.1)]

        self._trace1 = {
            "x": np.arange(74),
            "y": np.arange(74),
            "z": self._thedata[0],
            "colorscale": colorscale,
            "showlegend": False,
            "type": "heatmap"
        }
        self._data = go.Data([self._trace1])
        #        self._trace2 = {
        #            "x": np.arange(74),
        #            "y": np.arange(74),
        #            "z": self._theoverlay[0],
        #            "opacity": 0.3,
        #            "showlegend": False,
        #            "type": "heatmap"
        #        }
        #        self._data = go.Data([self._trace1, self._trace2])

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
