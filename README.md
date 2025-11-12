# EZ-AR: A universal AR application for multi-model visualization and real-time tracking in healthcare settings
This repository has been created by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid.

## 📝 Project Overview

This repository contains everything you need to get EZ-AR, a novel Augmented Reality (AR) application developed for **Microsoft HoloLens 2**. EZ-AR serves as a **universal, user-friendly platform that enables non-technical clinical users to visualize personalized 3D models** (derived from CT, MRI, PET, etc.) **and perform real-time object tracking in healthcare environments**.

The system is designed to **democratize the use of AR in the clinic by automating complex configuration and deployment tasks**, ensuring low latency, high reliability, and smooth interaction. Our work addresses the common barriers to widespread AR adoption by providing a robust and accessible method for model registration and visualization.

## 💻 Requirements and Setup
The project was developed and tested using the following environment:
| Component | Version / Platform | Notes |
| :--- | :--- | :--- |
| AR Platform | Microsoft HoloLens 2 | Head-mounted display for AR |
| Game Engine | Unity 2021.3.20f1 LTS | Long-Term Support version used for development |
| AR Framework | Mixed Reality Toolkit (MRTK) 2.7.3+ | Essential for interactions and user interface |
| Language | C# | Main application logic |

## 📄 Scientific Publication and Citation

This repository complements the following paper: 
- Title: EZ-AR: A universal AR application for multi-model visualization and real-time tracking in healthcare settings.
- Authors: Alicia Pose-Díez-de-la-Lastra, Gemma Arce-Alonso, José-Antonio Calvo-Haro, Rubén Pérez-Mañanes, Javier Pascau.
- Journal: [PENDING acceptance in Journal: Virtual Reality]
- DOI: [PENDING]
Please cite our paper if you use this code or any part of this work in your projects or publications:

## 🛠️ Repository Structure
The repository is organized as follows:
- 3D models folder: Contains the 3D models associated with two AR markers (to be used with Vuforia and regular QR tracking) and other models employed during the validation of our system.
- EZ-AR - App HoloLens 2: This is the EZ-AR app you have to install in your HoloLens 2 headset. Please, refer to section *Installation and usage* to know how to install it and set it up.
- EZ-AR - 3D Slicer module: This is the module in 3D Slicer that complements the EZ-AR app in HoloLens 2. Please, refer to section *Installation and usage* to know how to use this module.

## 🚀 Installation and Usage

Please, follow the instructions in the following video to setup your own personalized AR app: [insert url to YouTube]

## 📧 Contact

For any questions or inquiries regarding the project, please contact the corresponding author or the leader of the IGT research group, from Departamento de Bioingeniería, Universidad Carlos III de Madrid (UC3M).:

- Alicia Pose-Díez-de-la-Lastra (Corresponding Author): apose@ing.uc3m.es

- Javier Pascau (Senior Author): jpascau@ing.uc3m.es

For more information about the research group, feel free to have a look at our website: https://igt.uc3m.es/.

## 🙏 Acknowledgements

Research supported by projects TED2021-129392B-I00, TED2021-132200B-I00 and PID2023-149604OB-I00 (MCIU/AEI/10.13039/501100011033 and European Union “NextGenerationEU”/PRTR) and Comunidad de Madrid (MAGERIT-CM TEC-2024/COM-44 and Multiannual Agreement with UC3M SAFEDELIVERY-CM-UC3M).
