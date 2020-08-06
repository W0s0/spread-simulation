# Examining the impact of transaction cost at Momentum and Contrarian Strategies

This project opts to simulate Contrarian and Momentum strategies over a specified period in order to examine the impact of the transaction cost. In this implementation transaction costs are calculated via Roll’s model. 

## Data
The stock data are stored as a filesystem database which is created via dataDownload.m matlab file.

## Required packages:
1. datetime
2. argparse
3. backtrader
4. pandas
5. collections
6. random
7. shutil
8. matplotlib<=3.2.2

## Set up
1.	Make sure you have python 3 installed.
2.	Cd to the project directory and execute
`pip install -r requirements.txt `

## Execution
The following files and folders should exist inside the working directory in order to execute:
1. LIBOR USD-3.csv
2. libor.py
3. myIndicators.py
4. mystrategies.py
5. Simulation.py
6. Database

To execute you can either modify the predefined example at Simulation.py and execute the file Simulation.py as a python script or 
Import Simulation.py as a module and create your own scenario.