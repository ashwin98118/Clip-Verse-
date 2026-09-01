const fileInput = document.getElementById("file");
const selectedFile = document.getElementById("selectedFile");
const formatOptions = document.querySelectorAll(".format-option");
const formatInputs = document.querySelectorAll(
    'input[name="format"]'
);
const qualitySection = document.getElementById("qualitySection");


// ==========================================
// SHOW SELECTED FILE NAME
// ==========================================

if (fileInput) {

    fileInput.addEventListener("change", function () {

        if (this.files.length > 0) {

            const file = this.files[0];

            const sizeMB =
                (file.size / 1024 / 1024).toFixed(2);

            selectedFile.innerHTML =
                "📁 Selected: <strong>" +
                file.name +
                "</strong> (" +
                sizeMB +
                " MB)";

        }

    });

}


// ==========================================
// MP4 / MP3 FORMAT SELECTION
// ==========================================

formatInputs.forEach(function (input) {

    input.addEventListener("change", function () {

        formatOptions.forEach(function (option) {

            option.classList.remove("active");

        });


        const parentOption =
            this.closest(".format-option");

        if (parentOption) {

            parentOption.classList.add("active");

        }


        // Hide quality options for MP3

        if (this.value === "mp3") {

            qualitySection.style.display = "none";

        } else {

            qualitySection.style.display = "block";

        }

    });

});


// ==========================================
// DRAG AND DROP EFFECT
// ==========================================

const uploadBox = document.getElementById("uploadBox");

if (uploadBox && fileInput) {

    uploadBox.addEventListener("dragover", function (event) {

        event.preventDefault();

        uploadBox.style.borderColor = "#38bdf8";

        uploadBox.style.background =
            "rgba(56, 189, 248, 0.12)";

    });


    uploadBox.addEventListener("dragleave", function () {

        uploadBox.style.borderColor = "";

        uploadBox.style.background = "";

    });


    uploadBox.addEventListener("drop", function (event) {

        event.preventDefault();

        uploadBox.style.borderColor = "";

        uploadBox.style.background = "";

        if (event.dataTransfer.files.length > 0) {

            fileInput.files =
                event.dataTransfer.files;

            const changeEvent =
                new Event("change");

            fileInput.dispatchEvent(changeEvent);

        }

    });

}


// ==========================================
// PREVENT DOUBLE SUBMISSION
// ==========================================

const converterForm =
    document.querySelector("form");

if (converterForm) {

    converterForm.addEventListener(
        "submit",
        function () {

            const button =
                document.querySelector(
                    ".convert-button"
                );

            if (button) {

                button.disabled = true;

                button.innerHTML =
                    "⏳ Converting... Please wait";

            }

        }
    );

}
