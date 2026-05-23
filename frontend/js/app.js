const API_BASE = "http://localhost:8000/api";

// Initialize UI Hooks on load
document.addEventListener("DOMContentLoaded", () => {
    fetchStats();
    fetchAccounts();
    fetchLeads();
    fetchSettings();
    initializeLogStream();
});

// Helper: Open and Close Modals
function openModal(id) {
    document.getElementById(id).classList.remove("hidden");
    document.getElementById(id).classList.add("flex");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("flex");
    document.getElementById(id).classList.add("hidden");
}

// 1. Fetch Aggregated Metrics
async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE}/dashboard/stats`);
        const stats = await res.json();
        
        document.getElementById("statTotalLeads").innerText = stats.total_leads;
        document.getElementById("statActiveAccounts").innerText = stats.active_accounts;
        document.getElementById("statDmedLeads").innerText = stats.dmed_leads;
        document.getElementById("statRepliedLeads").innerText = stats.replied_leads;
        
        // Handle Play/Pause Campaign Button UI State
        const toggleBtn = document.getElementById("toggleCampaignBtn");
        const icon = toggleBtn.querySelector("i");
        const text = toggleBtn.querySelector("span");
        
        if (stats.campaign_running) {
            toggleBtn.className = "px-5 py-2.5 rounded-xl font-medium tracking-wide shadow-lg transition duration-300 transform hover:scale-105 flex items-center space-x-2 bg-gradient-to-r from-red-500 to-rose-600 text-white shadow-rose-500/20";
            icon.className = "fa-solid fa-pause";
            text.innerText = "Pause Campaign";
        } else {
            toggleBtn.className = "px-5 py-2.5 rounded-xl font-medium tracking-wide shadow-lg transition duration-300 transform hover:scale-105 flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-emerald-500/20";
            icon.className = "fa-solid fa-play";
            text.innerText = "Launch Automation";
        }
    } catch (e) {
        console.error("Error fetching metrics:", e);
    }
}

// 2. Fetch Profiles & Render
async function fetchAccounts() {
    try {
        const res = await fetch(`${API_BASE}/accounts`);
        const accounts = await res.json();
        const container = document.getElementById("accountsContainer");
        container.innerHTML = "";
        
        accounts.forEach(acc => {
            const div = document.createElement("div");
            div.className = "bg-slate-900/40 border border-white/5 rounded-xl p-3 flex justify-between items-center text-xs";
            
            const badgeClass = acc.status === "Active" ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400";
            
            div.innerHTML = `
                <div class="space-y-1">
                    <p class="font-medium text-white flex items-center">
                        <i class="fa-solid fa-user-circle text-slate-400 mr-1.5"></i> @${acc.username}
                    </p>
                    <p class="text-[10px] text-slate-400 flex items-center">
                        <i class="fa-solid fa-globe mr-1"></i> Proxy: ${acc.proxy ? acc.proxy.split('@')[1] || acc.proxy : 'Direct Web'}
                    </p>
                </div>
                <div class="text-right space-y-1">
                    <span class="px-2 py-0.5 rounded-full text-[9px] font-medium uppercase tracking-wider ${badgeClass}">${acc.status}</span>
                    <p class="text-[9px] text-slate-400">DMs: ${acc.daily_actions?.dm || 0} | Lks: ${acc.daily_actions?.like || 0}</p>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (e) {
        console.error("Error fetching accounts:", e);
    }
}

// 3. Fetch CRM Leads Database
async function fetchLeads() {
    try {
        const res = await fetch(`${API_BASE}/leads`);
        const leads = await res.json();
        const body = document.getElementById("leadsTableBody");
        body.innerHTML = "";
        
        leads.forEach(lead => {
            const tr = document.createElement("tr");
            tr.className = "border-b border-white/5 hover:bg-white/5 transition duration-150";
            
            let statusBadge = "";
            if (lead.status === "Pending") statusBadge = '<span class="bg-slate-500/20 text-slate-400 px-2 py-0.5 rounded text-[10px] uppercase font-mono">Pending</span>';
            else if (lead.status === "DMed") statusBadge = '<span class="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded text-[10px] uppercase font-mono">Outreach Sent</span>';
            else if (lead.status === "Replied") statusBadge = '<span class="bg-violet-500/20 text-violet-400 px-2 py-0.5 rounded text-[10px] uppercase font-mono">Replied</span>';
            else if (lead.status === "Failed") statusBadge = '<span class="bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded text-[10px] uppercase font-mono">Failed</span>';
            else statusBadge = `<span class="bg-brand-500/20 text-brand-300 px-2 py-0.5 rounded text-[10px] uppercase font-mono">${lead.status}</span>`;

            // Standardize username formatting (strip extra @)
            const cleanUser = lead.username.replace(/^@+/, "");

            tr.innerHTML = `
                <td class="p-3 text-white font-medium flex items-center space-x-2">
                    <span>@${cleanUser}</span>
                    <a href="https://www.instagram.com/${cleanUser}/" target="_blank" class="text-slate-500 hover:text-brand-400 transition" title="Open Instagram Profile">
                        <i class="fa-solid fa-external-link text-xs"></i>
                    </a>
                </td>
                <td class="p-3 text-slate-400 text-xs">${lead.niche}</td>
                <td class="p-3">
                    <select onchange="updateLeadStatus('${lead._id}', this.value)" class="bg-slate-900 border border-white/5 text-xs rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-brand-500">
                        <option value="Pending" ${lead.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="DMed" ${lead.status === 'DMed' ? 'selected' : ''}>Outreach Sent</option>
                        <option value="Replied" ${lead.status === 'Replied' ? 'selected' : ''}>Replied</option>
                        <option value="Failed" ${lead.status === 'Failed' ? 'selected' : ''}>Failed</option>
                    </select>
                </td>
                <td class="p-3">
                    <button onclick="copyPitchToClipboard('${cleanUser}', '${lead.niche}')" class="bg-brand-600/30 text-brand-300 border border-brand-500/20 px-2.5 py-1 rounded text-xs hover:bg-brand-600/50 transition flex items-center space-x-1">
                        <i class="fa-regular fa-copy"></i>
                        <span>Copy Pitch</span>
                    </button>
                </td>
            `;
            body.appendChild(tr);
        });
    } catch (e) {
        console.error("Error fetching leads:", e);
    }
}

// 3.5 Update Lead status in database
async function updateLeadStatus(id, newStatus) {
    try {
        await fetch(`${API_BASE}/leads/status`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lead_id: id, status: newStatus })
        });
        fetchStats();
    } catch (e) {
        console.error("Error updating status:", e);
    }
}

// Helper: Copy formulated pitch straight to clipboard
async function copyPitchToClipboard(username, niche) {
    try {
        const res = await fetch(`${API_BASE}/ai/preview`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, niche })
        });
        const data = await res.json();
        
        // Write to clipboard
        await navigator.clipboard.writeText(data.dm);
        
        alert(`B2B personalized pitch for @${username} copied to clipboard successfully! Paste it on Instagram.`);
    } catch (e) {
        console.error("Failed to copy B2B pitch:", e);
        alert("Make sure your Groq API key is valid to auto-generate the pitch!");
    }
}

// 4. Fetch Campaign Settings Config
async function fetchSettings() {
    try {
        const res = await fetch(`${API_BASE}/settings`);
        const config = await res.json();
        
        document.getElementById("campaignName").value = config.campaign_name || "";
        document.getElementById("maxLeads").value = config.max_leads_per_day || 30;
        document.getElementById("warmupMode").checked = config.safety_warmup_mode || false;
    } catch (e) {
        console.error("Error loading config:", e);
    }
}

// 5. Submit New Outreach Profile Account
async function submitAccount(e) {
    e.preventDefault();
    const username = document.getElementById("accUser").value;
    const password = document.getElementById("accPass").value;
    const proxy = document.getElementById("accProxy").value;
    
    try {
        const res = await fetch(`${API_BASE}/accounts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password, proxy })
        });
        if (res.ok) {
            closeModal("accountModal");
            document.getElementById("accUser").value = "";
            document.getElementById("accPass").value = "";
            document.getElementById("accProxy").value = "";
            fetchAccounts();
            fetchStats();
        } else {
            alert("Error validating or uploading Instagram account settings.");
        }
    } catch (err) {
        console.error(err);
    }
}

// 6. Submit New Lead target to database
async function submitLead(e) {
    e.preventDefault();
    const username = document.getElementById("leadUser").value;
    const niche = document.getElementById("leadNiche").value;
    
    try {
        const res = await fetch(`${API_BASE}/leads`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, niche })
        });
        if (res.ok) {
            closeModal("leadModal");
            document.getElementById("leadUser").value = "";
            fetchLeads();
            fetchStats();
        } else {
            alert("Lead username is already stored in CRM.");
        }
    } catch (err) {
        console.error(err);
    }
}

// 7. Save Global campaign settings update
async function saveSettings(e) {
    e.preventDefault();
    const campaign_name = document.getElementById("campaignName").value;
    const max_leads_per_day = parseInt(document.getElementById("maxLeads").value);
    const safety_warmup_mode = document.getElementById("warmupMode").checked;
    
    try {
        await fetch(`${API_BASE}/settings`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                campaign_name,
                max_leads_per_day,
                safety_warmup_mode,
                dm_template: "", // Updated through API
                comment_template: ""
            })
        });
        alert("Campaign limits successfully updated.");
        fetchStats();
    } catch (e) {
        console.error(e);
    }
}

// 8. Groq Real-Time Copywriter Generator Preview
async function previewAICopy() {
    const username = document.getElementById("previewUsername").value;
    const niche = document.getElementById("previewNiche").value;
    const spinner = document.getElementById("previewSpinner");
    
    if (!username) {
        alert("Please enter a target account name first.");
        return;
    }
    
    spinner.classList.remove("hidden");
    try {
        const res = await fetch(`${API_BASE}/ai/preview`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, niche })
        });
        const data = await res.json();
        
        document.getElementById("previewDmResult").innerText = data.dm;
        document.getElementById("previewCommentResult").innerText = data.comment;
    } catch (e) {
        console.error("AI preview error:", e);
    } finally {
        spinner.classList.add("hidden");
    }
}

// 9. Launch / Pause Campaign Engine
async function toggleCampaign() {
    try {
        const res = await fetch(`${API_BASE}/campaign/toggle`, { method: "POST" });
        const data = await res.json();
        fetchStats();
    } catch (e) {
        console.error(e);
    }
}

// 10. Server-Sent Events Logs stream reader
function initializeLogStream() {
    const terminal = document.getElementById("terminalStream");
    const source = new EventSource(`${API_BASE}/logs/stream`);
    
    source.onmessage = (event) => {
        const log = JSON.parse(event.data);
        const div = document.createElement("div");
        
        let colorClass = "text-slate-300";
        if (log.level === "SUCCESS") colorClass = "text-emerald-400";
        else if (log.level === "WARNING") colorClass = "text-amber-400";
        else if (log.level === "ERROR") colorClass = "text-rose-400";
        
        const timestamp = new Date(log.timestamp).toLocaleTimeString();
        
        div.className = colorClass;
        div.innerHTML = `[${timestamp}] [${log.level}] ${log.message}`;
        terminal.appendChild(div);
        
        // Auto scroll to bottom
        terminal.scrollTop = terminal.scrollHeight;
    };
    
    source.onerror = () => {
        console.warn("Log SSE stream disconnected. Retrying...");
    };
}
