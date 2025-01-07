# User Interface (UI) Manual for PanelApp Patient Search

## Table of Contents
1. [Introduction](#introduction)
2. [Purpose](#purpose)
3. [System Requirements](#system-requirements)
4. [UI Components Overview](#ui-components-overview)
5. [Common User Interactions](#common-user-interactions)
6. [Troubleshooting UI Issues](#troubleshooting-ui-issues)
7. [Best Practices](#best-practices)
8. [Feedback and Support](#feedback-and-support)

---

## Introduction
The **PanelApp Patient Search** UI allows users to efficiently search for patient information or R Codes, manage patient data, and analyse clinical details using an intuitive interface.

## Purpose
This manual provides guidance on:
- Navigating the user interface effectively.
- Performing common tasks such as searching for patient IDs or R Codes, adding new records, and exporting data.
- Troubleshooting common UI-related issues.

## System Requirements
To use the UI effectively, ensure your system meets the following requirements:
- **Supported Browsers**: Google Chrome (v90+), Mozilla Firefox (v85+), Safari (v13+), or Microsoft Edge (v89+).
- **Screen Resolution**: Minimum resolution of 1280x720 for optimal layout.
- **Network**: Reliable internet connection for cloud-based interactions.

---

## UI Components Overview

### 1. **Form Section**
- **Purpose**: Allows users to search for patient IDs or R Codes.
- **Components**:
  - Dropdown menu to select search type (Patient ID or R Code).
  - Input field for entering search queries.
  - Submit button to perform the search.

### 2. **Results Section**
- **Purpose**: Displays the results of user searches.
- **Components**:
  - Dynamically populated table with search results.
  - Buttons for further actions like adding new entries.

### 3. **Modals**
- **Purpose**: Collect additional user input or confirm actions.
- **Examples**:
  - Modal for adding new R Codes.
  - Modal for entering new patient IDs.

### 4. **Footer**
- **Purpose**: Displays copyright information.

---

## Common User Interactions

### Searching for Patient or R Code
- Select the search type (Patient ID or R Code) using the dropdown menu in the **Form Section**.
- Enter the search query in the input field.
- Click the **Search** button to view results in the **Results Section**.

### Adding R Code to Patient
- Search for a patient ID in the **Form Section**.
- If the patient exists, a button labelled **Add a new R Code analysis** will appear in the **Results Section**.
- Click the button to open the modal, enter the R Code, and submit.

### Adding Patient to R Code
- Search for an R Code in the **Form Section**.
- If the R Code exists but is not associated with any patients, a button labelled **Add a new patient** will appear in the **Results Section**.
- Click the button to open the modal, enter the patient ID(s) (comma-separated for multiple patients), and submit.

### Adding R Code That Does Not Exist in Database
- Search for an R Code in the **Form Section**.
- If the R Code does not exist, the system will prompt you to add it and associate it with one or more patients.
- Use the modal to enter the R Code and a list of patient IDs (comma-separated for multiple patients), then submit.

### Comparing Gene Panel Data
- In the **Results Section**, locate the **Compare to Live PanelApp** option in the dynamically populated table.
- Click the **Compare** button next to the relevant entry.
- A confirmation modal will appear, indicating the operation may take some time.
- Confirm the comparison to proceed.
- View the results in a modal showing the differences (added or removed items) between the local data and the live PanelApp data.
---

## Troubleshooting UI Issues

### Search Function Not Responding
- **Steps to Resolve**:
  - Ensure the input field is not empty.
  - Refresh the page if the search does not respond.

### Modals Not Displaying
- **Steps to Resolve**:
  - Verify that JavaScript is enabled in your browser.
  - Clear your browser cache and reload the page.

### Results Not Loading
- **Steps to Resolve**:
  - Check your internet connection.
  - Ensure the server is running if using a local setup.

---

## Best Practices

1. **Keep Your Browser Updated**: Ensure you’re using the latest version for full compatibility.
2. **Provide Accurate Inputs**: Use the correct format for Patient IDs (e.g., `Patient_123`) and R Codes (e.g., `R123`).
3. **Refresh Periodically**: Refresh the page to ensure the latest data is displayed.

---

## Feedback and Support
We value your feedback to improve the UI experience. If you encounter issues or have suggestions:
- **Submit Feedback**: Use the feedback form in the application footer.
- **Contact Support**: Email us at **PanelAppPatientSearch@support.com** for assistance.

---

