const urlInput = document.getElementById("url");
const downloadForm = document.querySelector(".download-form");
const pasteButton = document.querySelector(".paste-button");

async function pasteURL() {
    if (!urlInput) return;

    try {
        const text = await navigator.clipboard.readText();

        if (text) {
            urlInput.value = text;
            urlInput.focus();
        }
    } catch (error) {
        urlInput.focus();
    }
}

if (pasteButton) {
    pasteButton.addEventListener("click", pasteURL);
}

if (downloadForm) {
    downloadForm.addEventListener("submit", function () {

        if (!urlInput || !urlInput.value.trim()) {
            return;
        }

        const button = downloadForm.querySelector(".download-button");

        if (button) {
            button.disabled = true;
            button.innerHTML = "⏳ Processing...";
        }
    });
}
