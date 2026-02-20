/* ── Toast Notifications ──────────────────────────────────── */

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => {
        toast.className = "toast hidden";
    }, 2800);
}

/* ── Save Dropdown ────────────────────────────────────────── */

let activeDropdown = null;

function toggleSaveDropdown(btn, jobId) {
    const wrapper = btn.closest(".save-dropdown-wrapper");
    const dropdown = wrapper.querySelector(".save-dropdown");

    if (activeDropdown && activeDropdown !== dropdown) {
        activeDropdown.classList.add("hidden");
    }

    dropdown.classList.toggle("hidden");
    activeDropdown = dropdown.classList.contains("hidden") ? null : dropdown;
}

document.addEventListener("click", (e) => {
    if (activeDropdown && !e.target.closest(".save-dropdown-wrapper")) {
        activeDropdown.classList.add("hidden");
        activeDropdown = null;
    }
});

/* ── Save / Unsave ────────────────────────────────────────── */

async function saveToList(jobId, listName, btnEl) {
    try {
        const resp = await fetch("/api/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: jobId, list_name: listName }),
        });
        const data = await resp.json();

        if (resp.ok) {
            const card = document.querySelector(`.job-card[data-job-id="${jobId}"]`);
            if (card) {
                const saveBtn = card.querySelector(".btn-save");
                saveBtn.classList.add("saved");
                saveBtn.textContent = "★";
            }
            showToast(`Saved to "${listName}"`);
        } else {
            showToast(data.error || "Failed to save", "error");
        }
    } catch (e) {
        showToast("Network error", "error");
    }

    if (activeDropdown) {
        activeDropdown.classList.add("hidden");
        activeDropdown = null;
    }
}

async function unsaveJob(jobId, listName = "") {
    try {
        const resp = await fetch("/api/unsave", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_id: jobId, list_name: listName }),
        });

        if (resp.ok) {
            if (window.location.pathname.startsWith("/saved")) {
                const card = document.querySelector(`.job-card[data-job-id="${jobId}"]`);
                if (card) {
                    card.style.transition = "opacity 200ms, transform 200ms";
                    card.style.opacity = "0";
                    card.style.transform = "translateX(20px)";
                    setTimeout(() => card.remove(), 220);
                }
            } else {
                const card = document.querySelector(`.job-card[data-job-id="${jobId}"]`);
                if (card) {
                    const saveBtn = card.querySelector(".btn-save");
                    saveBtn.classList.remove("saved");
                    saveBtn.textContent = "☆";
                }
            }
            showToast("Removed from saved");
        }
    } catch (e) {
        showToast("Network error", "error");
    }

    if (activeDropdown) {
        activeDropdown.classList.add("hidden");
        activeDropdown = null;
    }
}

/* ── Create New List ──────────────────────────────────────── */

async function createAndSave(jobId) {
    const name = prompt("Enter list name:");
    if (!name || !name.trim()) return;

    try {
        await fetch("/api/lists", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name.trim() }),
        });
        await saveToList(jobId, name.trim());
    } catch (e) {
        showToast("Failed to create list", "error");
    }
}

async function createNewList() {
    const name = prompt("Enter list name:");
    if (!name || !name.trim()) return;

    try {
        const resp = await fetch("/api/lists", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name.trim() }),
        });

        if (resp.ok) {
            showToast(`List "${name.trim()}" created`);
            setTimeout(() => location.reload(), 500);
        } else {
            const data = await resp.json();
            showToast(data.error || "Failed", "error");
        }
    } catch (e) {
        showToast("Network error", "error");
    }
}

/* ── Trigger Scrape ───────────────────────────────────────── */

async function triggerScrape() {
    const btn = document.getElementById("btn-scrape");
    btn.classList.add("loading");
    btn.disabled = true;

    try {
        const resp = await fetch("/api/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({}),
        });

        if (resp.ok) {
            showToast("Scraping started! Refresh in ~30s to see new jobs.");
            setTimeout(() => {
                btn.classList.remove("loading");
                btn.disabled = false;
                location.reload();
            }, 25000);
        }
    } catch (e) {
        showToast("Failed to start scrape", "error");
        btn.classList.remove("loading");
        btn.disabled = false;
    }
}
