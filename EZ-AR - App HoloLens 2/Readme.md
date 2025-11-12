# EZ-AR: a user-friendly app for Microsoft HoloLens 2

## How to download and install the app in your device
To start, you must own a Microsoft HoloLens 2 headset configured in Developer Mode. Then, follow the steps below:
1. Download this folder into the local storage of your computer.
2. Turn on your HoloLens 2, connect to the same network as your PC and find its IP address. In [insert video Setup Instructions] you have an example on how to get it using the HoloRemoting app (min 02:35).
3. Copy the IP addreess (shown in yellow) into a web browser in your PC. You will be asked to sign in with your HoloLens 2 user name and password. The Windows Device Portal will pop up for you.
<img width="611" height="339" alt="image" src="https://github.com/user-attachments/assets/94e28672-011e-4536-be87-37906a36637d" />


## Microsoft HoloLens 2 app
After initialization, a generic user interface is displayed half a meter in front of the user (Figure 6A). This interface can be repositioned within the environment. The UI includes eight toggle buttons, each corresponding to a distinct virtual 3D model.

<img width="2710" height="1888" alt="Figure_UIapp" src="https://github.com/user-attachments/assets/89b4d48c-2c3a-4d4c-b263-fe92cec81c07" />

Figure 1: User interface of the EZ-AR application in Microsoft HoloLens 2. (A) Unconfigured control panel displayed before any 3D virtual models are loaded. (B) Control panel adjusted after loading four personalized 3D virtual models.

Below you can find details on the functionality of each UI element:

- *Load Models* button: Must always be pressed first, initializing the application according to the user-defined parameters. When clicked, it downloads the virtual 3D models from Google Drive using the direct download URLs provided in the configuration file created with the EZ-AR setup module in 3D Slicer. 

The downloaded models are stored in the headset's local storage, eliminating the need for an internet connection in future sessions. This means that the **access to the internet is only required during the initial setup**. Once the downloading process is complete, tracking of the desired AR reference marker begins. 
**The 3D virtual models are automatically instantiated in their corresponding positions in the real space with their assigned colors**. The model names specified in the configuration file are mapped, in order, to the corresponding toggle buttons. If fewer than eight models are defined, the unused buttons are removed, and the layout of the interface is adjusted to fill the designated space evenly (Figure 1B). 

On the right side of the control panel, a set of interactive elements allows users to apply visualization adjustments to individual models by selecting the corresponding toggle button beforehand. The *All Models* button can be used to apply any of these settings to all models simultaneously. The options are:
- The *Visibility toggle* button lets users show or hide a selected model.
- The *Opacity slider* controls the transparency of the models.
- The *Manipulation toggle* switch converts the virtual 3D models into fully interactive objects that can be grabbed, translated, rotated, and scaled using hand gestures. When this option is turned off, the models remain anchored and move only with respect to the AR reference marker. The *Manipulation* functionality may be particularly useful in surgical contexts. For example, to temporarily enlarge anatomical structures that are difficult to interpret.

- *Reset Pose* button: Models can be restored to their original pose relative to the AR reference marker at any time by pressing this button.
- *Toggle tracking* toggle: The application also allows users to toggle the tracking capability of the headset, enabling or disabling the detection of the AR reference marker as needed.
- *Clear Memory* button: It erases all downloaded content from the device’s local storage. This feature is intended to facilitate the loading of a new configuration file, for instance, when switching to data from a different patient.

## Sample use cases
You can see some sample use cases in the following video: [Insert URL Youtube video: Supp. Video 2: Sample Use Cases]
