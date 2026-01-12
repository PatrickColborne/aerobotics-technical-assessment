# aerobotics-technical-assessment

## Overview

This repository is my implementation of the Aerobotics technical assessment. It contains an application that identifies
missing trees in an orchard. The orchard data is retrieved from Aerobotics' API, and the application processes this data
to find any missing trees based on their expected positions in the orchard rows.

## Public Endpoint

**Base URL:**  
https://aerobotics-n2j43.ondigitalocean.app/

**Path:**  
`/orchards/{orchard_id}/missing-trees`

**Operation Name:**  
`getMissingTrees`

### Description
This endpoint retrieves missing tree data for a specific orchard.

- **Method:** `GET`  
- **Path Parameter:**  
  - `orchard_id` — The ID of the orchard to query for missing trees.  
- **Headers:**  
  - `Authorization: Bearer <YOUR_API_KEY>` — Required for authentication.

## Improvements to Be Made

- Add more comprehensive unit and integration tests.
- Performance improvements:
    - Optimise the algorithm to handle larger datasets more efficiently.
    - The current algorithm assumes orchard rows are straight, which is not always true. A more robust approach would be
      to fit a polynomial regression for each orchard row and use it to index trees and identify missing trees.
- I have primarily used Python as a scripting language in the past. I have lots to learn still.
- Create a GitHub workflow to automate testing and application deployment.

# Visualize the application

In order to visualise the orchard and the position of the missing trees, I created the following script:

`visualise_missing_trees.py`

It prints a picture of the orchard to the console with the missing trees represented by 'X'. This just makes it easier
to visualise the missing trees.
