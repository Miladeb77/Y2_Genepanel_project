document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("search-form");
    const resultsDiv = document.getElementById("results");
    const modal = document.getElementById("rcode-modal");
    const modalMessage = document.getElementById("modal-message");
    const yesButton = document.getElementById("yes-btn");
    const noButton = document.getElementById("no-btn");
    
    // Existing modals...
    const rcodeInputModal = document.getElementById("rcode-input-modal");
    const rcodeInputBox = document.getElementById("rcode-input-box");
    const rcodeSubmitBtn = document.getElementById("rcode-submit-btn");
    const rcodeCancelBtn = document.getElementById("rcode-cancel-btn");

    const patientIDInputModal = document.getElementById("patient-id-input-modal");
    const patientIDInputBox = document.getElementById("patient-id-input-box");
    const patientIDSubmitBtn = document.getElementById("patient-id-submit-btn");
    const patientIDCancelBtn = document.getElementById("patient-id-cancel-btn");

    const addPatientBtn = document.getElementById("add-patient-btn");
    const addPatientModal = document.getElementById("add-patient-modal");
    const addPatientIdInput = document.getElementById("add-patient-id-input");
    const addPatientSubmitBtn = document.getElementById("add-patient-submit-btn");
    const addPatientCancelBtn = document.getElementById("add-patient-cancel-btn");

    const invalidFormatModal = document.getElementById("invalid-format-modal");
    const invalidFormatOkBtn = document.getElementById("invalid-format-ok-btn");

    // New elements for R code analysis feature
    const addRCodeBtn = document.getElementById("add-r-code-btn");
    const addRCodeModal = document.getElementById("add-r-code-modal");
    const addRCodeInput = document.getElementById("add-r-code-input");
    const addRCodeSubmitBtn = document.getElementById("add-r-code-submit-btn");
    const addRCodeCancelBtn = document.getElementById("add-r-code-cancel-btn");
    const invalidRCodeModal = document.getElementById("invalid-r-code-modal");
    const invalidRCodeOkBtn = document.getElementById("invalid-r-code-ok-btn");

    const searchTypeSelect = document.getElementById("search-type");

    let currentRCode = null;     // Store the current R Code searched, if any
    let currentPatientId = null; // Store the current Patient ID searched, if any
    let currentResultsData = null; // Store current result data if needed

    // New elements for the comparison feature
    const compareConfirmationModal = document.getElementById("compare-confirmation-modal");
    const compareConfirmYesBtn = document.getElementById("compare-confirm-yes-btn");
    const compareConfirmNoBtn = document.getElementById("compare-confirm-no-btn");
    const compareWaitModal = document.getElementById("compare-wait-modal");
    const compareResultsModal = document.getElementById("compare-results-modal");
    const compareResultsContent = document.getElementById("compare-results-content");

    let currentClinicalIdToCompare = null;
    let currentHGNCIDsToCompare = null;

    searchTypeSelect.addEventListener("change", () => {
        if (searchTypeSelect.value === "patient_id") {
            addPatientBtn.style.display = "none";
            addRCodeBtn.style.display = "none";
        } else if (searchTypeSelect.value === "r_code") {
            addRCodeBtn.style.display = "none";
            addPatientBtn.style.display = "none";
        }
    });

    /**
     * After successfully fetching data by patient_id, show the "Add a new R code analysis" button.
     * After successfully fetching data by r_code, show the "Add a new patient" button.
     */
    async function fetchDataForRCode(rCode) {
        const apiUrl = `/rcode?r_code=${encodeURIComponent(rCode)}`;
        const response = await fetch(apiUrl);
        if (response.ok) {
            const data = await response.json();
            currentRCode = rCode;
            currentPatientId = null; // Not a patient_id search
            renderTable(Array.isArray(data) ? data : [data]);
            addPatientBtn.textContent = `Add a new patient for R code ${rCode}`;
            addPatientBtn.style.display = "block"; // show Add a new patient button
            addRCodeBtn.style.display = "none";
        } else if (response.status === 404) {
            // R code not found handling...
            const errorData = await response.json();
            resultsDiv.innerHTML = "";
            addPatientBtn.style.display = "none";
            addRCodeBtn.style.display = "none";
            if (errorData.message && errorData.message.includes("not found")) {
                modalMessage.textContent = errorData.prompt || "No patients have had this R code analysis. Do you have any?";
                modal.style.display = "block";

                yesButton.onclick = () => {
                    modal.style.display = "none";
                    patientIDInputModal.style.display = "block";
                    document.getElementById("patient-id-input-message").textContent = 
                        "Please enter the patient ID(s). If there are multiple patient IDs, separate them by comma:";
                    patientIDInputBox.placeholder = "Patient_anydigit,Patient_anydigit,... or Patient_anydigit";
                    patientIDInputBox.value = "";

                    patientIDSubmitBtn.onclick = async () => {
                        const patientIdsInput = patientIDInputBox.value.trim();
                        if (!patientIdsInput) {
                            alert("Please provide at least one patient ID.");
                            return;
                        }
                
                        let patientIds = patientIdsInput.split(",").map(id => id.trim());
                
                        const patientIdPattern = /^Patient_\d+$/;
                        for (let pid of patientIds) {
                            if (!patientIdPattern.test(pid)) {
                                alert(`Invalid patient ID format detected: ${pid}. Please re-enter patient ID(s) in the correct format`);
                                return;
                            }
                        }
                
                        const uniquePatientIds = new Set(patientIds);
                        if (uniquePatientIds.size !== patientIds.length) {
                            alert("Some patient IDs have been added multiple times. Please provide unique patient IDs.");
                            return;
                        }
                
                        await handleRCodeCreation(rCode, patientIds);
                        patientIDInputModal.style.display = "none";
                    };
                
                    patientIDCancelBtn.onclick = () => {
                        patientIDInputModal.style.display = "none";
                        location.reload();
                    };
                };

                noButton.onclick = () => {
                    modal.style.display = "none";
                    location.reload();
                };
            } else if (errorData.message && errorData.message.includes("not a valid R code")) {
                alert("This is not a valid R code. Please enter a valid R code.");
                location.reload();
            } else {
                alert("An unexpected error occurred. Please try again.");
                location.reload();
            }
        } else {
            const errorData = await response.json();
            resultsDiv.innerHTML = `<p>Error: ${errorData.error}</p>`;
            addPatientBtn.style.display = "none";
            addRCodeBtn.style.display = "none";
        }
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const searchType = document.getElementById("search-type").value;
        const searchInput = document.getElementById("search-input").value.trim();
        resultsDiv.innerHTML = "<p>Loading...</p>";

        if (!searchInput) {
            alert("Invalid input. Please enter a valid Patient ID or R code.");
            resultsDiv.innerHTML = "";
            return;
        }

        if (searchType === "patient_id") {
            const apiUrl = `/patient?patient_id=${encodeURIComponent(searchInput)}`;
            try {
                const response = await fetch(apiUrl);
                if (response.ok) {
                    const data = await response.json();
                    currentPatientId = searchInput;
                    currentRCode = null;
                    renderTable(Array.isArray(data) ? data : [data]);
                    // Show "Add a new R code analysis" button when searching by patient_id
                    addRCodeBtn.textContent = `Add a new R code analysis for Patient ID ${searchInput}`;
                    addRCodeBtn.style.display = "block";
                    addPatientBtn.style.display = "none";
                } else if (response.status === 404) {
                    const errorData = await response.json();
                    resultsDiv.innerHTML = "";
                    addRCodeBtn.style.display = "none";
                    if (errorData.error === "Invalid Patient ID format.") {
                        alert(errorData.message || "Invalid Patient ID format.");
                    } else if (errorData.message && errorData.message.startsWith("No records found for Patient ID")) {
                        // Show the R code input modal to add a record
                        currentPatientId = searchInput;
                        currentRCode = null;
                        rcodeInputModal.style.display = "block";
                        rcodeInputBox.value = "";
                        document.getElementById("rcode-input-message").textContent = errorData.message;
                
                        rcodeSubmitBtn.onclick = async () => {
                            const rCode = rcodeInputBox.value.trim();
                            if (rCode) {
                                try {
                                    const createResponse = await fetch('/patient/add', {
                                        method: "POST",
                                        headers: {
                                            "Content-Type": "application/json",
                                        },
                                        body: JSON.stringify({
                                            patient_id: searchInput,
                                            r_code: rCode,
                                        }),
                                    });
                        
                                    const data = await createResponse.json();
                        
                                    if (createResponse.ok) {
                                        const fetchResponse = await fetch(`/patient?patient_id=${encodeURIComponent(searchInput)}`);
                                        if (fetchResponse.ok) {
                                            const fetchedData = await fetchResponse.json();
                                            rcodeInputModal.style.display = "none";
                                            renderTable(Array.isArray(fetchedData) ? fetchedData : [fetchedData]);
                                            // Show the "Add a new R code analysis" button now that patient exists
                                            addRCodeBtn.style.display = "block";
                                        } else {
                                            alert("Record created but could not fetch updated details.");
                                        }
                                    } else {
                                        // Invalid R Code or error
                                        alert(data.message || "Invalid R Code. Please enter a valid R Code.");
                                    }
                                } catch (error) {
                                    alert("An unexpected error occurred. Please try again.");
                                }
                            } else {
                                alert("R Code is required to create a new record.");
                            }
                        };
                
                        rcodeCancelBtn.onclick = () => {
                            rcodeInputModal.style.display = "none";
                            resultsDiv.innerHTML = "<p>Operation canceled.</p>";
                        };
                    } else {
                        alert("An unexpected error occurred. Please try again.");
                    }
                } else {
                    const errorData = await response.json();
                    resultsDiv.innerHTML = `<p>Error: ${errorData.error}</p>`;
                    addRCodeBtn.style.display = "none";
                }
            } catch (error) {
                resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
                addRCodeBtn.style.display = "none";
            }
        } else if (searchType === "r_code") {
            await fetchDataForRCode(searchInput);
        } else {
            resultsDiv.innerHTML = "<p>Invalid search type selected.</p>";
        }
    });

    // Handle Add a new R code analysis button
    addRCodeBtn.addEventListener("click", () => {
        if (!currentPatientId) {
            alert("No Patient ID found. Please search for a Patient ID first.");
            return;
        }
        addRCodeInput.value = "";
        addRCodeModal.style.display = "block";
    });

    addRCodeCancelBtn.addEventListener("click", () => {
        addRCodeModal.style.display = "none";
    });

    addRCodeSubmitBtn.addEventListener("click", async () => {
        const rCodeValue = addRCodeInput.value.trim();
        if (!rCodeValue) {
            alert("Please provide an R code.");
            return;
        }

        if (!currentPatientId) {
            alert("No Patient ID found. Please search for a Patient ID first.");
            return;
        }

        try {
            const createResponse = await fetch('/patient/add', {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    patient_id: currentPatientId,
                    r_code: rCodeValue
                })
            });

            const data = await createResponse.json();

            if (createResponse.ok) {
                // Successfully created, now re-fetch data for the same patient_id
                addRCodeModal.style.display = "none";
                const fetchResponse = await fetch(`/patient?patient_id=${encodeURIComponent(currentPatientId)}`);
                if (fetchResponse.ok) {
                    const fetchedData = await fetchResponse.json();
                    renderTable(Array.isArray(fetchedData) ? fetchedData : [fetchedData]);
                } else {
                    alert("Record created but could not fetch updated details. Try refreshing the page.");
                }
            } else {
                // Check if it's due to invalid R code
                if (data.error && data.error.includes("Invalid R Code") || data.message && data.message.includes("not a valid R Code")) {
                    addRCodeModal.style.display = "none";
                    invalidRCodeModal.style.display = "block";
                } else {
                    alert(data.error || "Error creating new record. Please try again.");
                }
            }
        } catch (error) {
            alert("An unexpected error occurred. Please try again.");
        }
    });

    invalidRCodeOkBtn.addEventListener("click", () => {
        invalidRCodeModal.style.display = "none";
        // Show the add R code modal again so the user can re-enter a valid R code
        addRCodeModal.style.display = "block";
    });

    addPatientBtn.addEventListener("click", () => {
        addPatientIdInput.value = "";
        addPatientModal.style.display = "block";
    });

    addPatientCancelBtn.addEventListener("click", () => {
        addPatientModal.style.display = "none";
    });

    addPatientSubmitBtn.addEventListener("click", async () => {
        const patientIdValue = addPatientIdInput.value.trim();
        const pattern = /^Patient_\d+$/;
        if (!pattern.test(patientIdValue)) {
            addPatientModal.style.display = "none";
            invalidFormatModal.style.display = "block";
        } else {
            try {
                const createResponse = await fetch('/patient/add', {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        patient_id: patientIdValue,
                        r_code: currentRCode
                    })
                });

                const data = await createResponse.json();

                if (createResponse.ok) {
                    addPatientModal.style.display = "none";
                    await fetchDataForRCode(currentRCode);
                } else {
                    alert(data.error || "Error creating new patient record.");
                }
            } catch (error) {
                alert("An unexpected error occurred. Please try again.");
            }
        }
    });

    invalidFormatOkBtn.addEventListener("click", () => {
        invalidFormatModal.style.display = "none";
        addPatientModal.style.display = "block";
    });

    async function handleRCodeCreation(rCode, patientIds) {
        try {
            const response = await fetch(`/rcode/handle`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    r_code: rCode,
                    patient_ids: patientIds,
                    response: "Yes",
                }),
            });
            const data = await response.json();

            if (response.ok) {
                renderTable(data.new_records);
            } else {
                resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
        }
    }

    function renderTable(data) {
        currentResultsData = data;
        const table = document.createElement("table");
        table.className = "results-table";

        const headerRow = document.createElement("tr");
        ["Patient ID", "Clinical ID", "Panel Version", "Test Date", "Panel Retrieved Date", "Gene Panel", "HGNC IDs", "Compare to Live panelApp"].forEach((header) => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
        table.appendChild(headerRow);

        data.forEach((row) => {
            const tableRow = document.createElement("tr");

            const patientIdCell = document.createElement("td");
            patientIdCell.textContent = row.patient_id || "N/A";
            tableRow.appendChild(patientIdCell);

            const clinicalIdCell = document.createElement("td");
            clinicalIdCell.textContent = row.relevant_disorders || "N/A";
            tableRow.appendChild(clinicalIdCell);

            const panelVersionCell = document.createElement("td");
            panelVersionCell.textContent = row.panel_version || "N/A";
            tableRow.appendChild(panelVersionCell);

            const testDateCell = document.createElement("td");
            testDateCell.textContent = row.test_date || "N/A";
            tableRow.appendChild(testDateCell);

            const panelRetrievedDateCell = document.createElement("td");
            panelRetrievedDateCell.textContent = row.panel_retrieved_date || "N/A";
            tableRow.appendChild(panelRetrievedDateCell);

            const genePanelCell = document.createElement("td");
            genePanelCell.textContent = row.gene_panel ? row.gene_panel.join(", ") : "N/A";
            tableRow.appendChild(genePanelCell);

            const hgncIdsCell = document.createElement("td");
            hgncIdsCell.textContent = row.hgnc_ids ? row.hgnc_ids.join(", ") : "N/A";
            tableRow.appendChild(hgncIdsCell);

            // Add Compare to Live panelApp Column
            const compareCell = document.createElement("td");
            if (row.relevant_disorders && row.hgnc_ids && row.hgnc_ids.length > 0) {
                const compareButton = document.createElement("button");
                compareButton.textContent = "Click to compare";
                compareButton.onclick = () => {
                    openCompareConfirmationModal(row.relevant_disorders, row.hgnc_ids);
                };
                compareCell.appendChild(compareButton);
            } else {
                compareCell.textContent = "N/A";
            }
            tableRow.appendChild(compareCell);

            table.appendChild(tableRow);
        });

        resultsDiv.innerHTML = "";
        resultsDiv.appendChild(table);
    }

    function openCompareConfirmationModal(clinicalId, hgncIDs) {
        currentClinicalIdToCompare = clinicalId;
        currentHGNCIDsToCompare = hgncIDs;
        compareConfirmationModal.style.display = "block";
    }

    compareConfirmYesBtn.onclick = async () => {
        compareConfirmationModal.style.display = "none";
        // Show wait modal
        compareWaitModal.style.display = "block";

        // Perform the comparison
        try {
            const response = await fetch('/compare-live-panelapp', {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    clinical_id: currentClinicalIdToCompare,
                    existing_hgnc_ids: currentHGNCIDsToCompare
                })
            });

            const data = await response.json();
            compareWaitModal.style.display = "none";

            if (response.ok) {
                // Show results
                if (data.message && data.differences) {
                    const { added, removed } = data.differences;
                    let resultHtml = `<h3>Differences Found</h3><p>${data.message}</p>`;
                    if (added && added.length > 0) {
                        resultHtml += `<p><strong>Added (in Live PanelApp but not in local):</strong> ${added.join(", ")}</p>`;
                    }
                    if (removed && removed.length > 0) {
                        resultHtml += `<p><strong>Removed (in local but not in Live PanelApp):</strong> ${removed.join(", ")}</p>`;
                    }
                    compareResultsContent.innerHTML = resultHtml;
                } else if (data.message) {
                    compareResultsContent.innerHTML = `<p>${data.message}</p>`;
                } else {
                    compareResultsContent.innerHTML = `<p>No changes found.</p>`;
                }

                compareResultsModal.style.display = "block";
            } else {
                alert(data.error || "An error occurred during comparison.");
            }

        } catch (error) {
            compareWaitModal.style.display = "none";
            alert("An error occurred during comparison: " + error.message);
        }
    };

    compareConfirmNoBtn.onclick = () => {
        compareConfirmationModal.style.display = "none";
    };

    window.addEventListener("click", (e) => {
        if (e.target === compareResultsModal) {
            compareResultsModal.style.display = "none";
        }
    });
});