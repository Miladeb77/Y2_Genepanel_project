document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("search-form");
    const resultsDiv = document.getElementById("results");
    const addPatientBtn = document.getElementById("add-patient-btn");
    const addConfirmationModal = document.getElementById("add-confirmation-modal");
    const addConfirmationMessage = document.getElementById("add-confirmation-message");
    const addConfirmYesBtn = document.getElementById("add-confirm-yes-btn");
    const addConfirmNoBtn = document.getElementById("add-confirm-no-btn");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        resultsDiv.innerHTML = "<p>Loading...</p>";
        // Simulate fetching data
        setTimeout(() => {
            resultsDiv.innerHTML = "<p>Results loaded successfully.</p>";
            addPatientBtn.style.display = "block";
        }, 1000);
    });

    addPatientBtn.addEventListener("click", () => {
        addConfirmationMessage.textContent = "This action will create a new patient record. Are you sure you want to proceed?";
        addConfirmationModal.style.display = "block";
    });

    addConfirmYesBtn.addEventListener("click", () => {
        addConfirmationModal.style.display = "none";
        alert("New patient record created.");
    });

    addConfirmNoBtn.addEventListener("click", () => {
        addConfirmationModal.style.display = "none";
    });
});
