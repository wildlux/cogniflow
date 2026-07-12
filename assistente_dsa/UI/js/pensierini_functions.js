// pensierini_functions.js
// Funzioni JavaScript per la gestione dei pensierini

function addWorkspacePensierino(text, workspacePensierini, workspacePensierinoInput, addLogMessage) {
    if (text.trim() !== "") {
        workspacePensierini.push({
            "text": text.trim(),
            "timestamp": new Date().toISOString()
        })
        workspacePensierinoInput.text = ""
        addLogMessage("INFO", "Pensierino aggiunto all'area di lavoro")
        return true
    }
    return false
}

function removeWorkspacePensierino(index, workspacePensierini, addLogMessage) {
    if (index >= 0 && index < workspacePensierini.length) {
        workspacePensierini.splice(index, 1)
        addLogMessage("INFO", "Pensierino rimosso dall'area di lavoro")
        return true
    }
    return false
}

function updateWorkspacePensierino(index, newText, workspacePensierini) {
    if (index >= 0 && index < workspacePensierini.length) {
        workspacePensierini[index].text = newText
        workspacePensierini[index].timestamp = new Date().toISOString()
        return true
    }
    return false
}

function readWorkspacePensierino(text, addLogMessage) {
    console.log("Lettura pensierino area di lavoro:", text)
    addLogMessage("INFO", "Lettura pensierino: " + text.substring(0, 30) + "...")
    // Qui potresti integrare con TTS
}

function exportWorkspacePensierini(workspacePensierini, addLogMessage) {
    if (workspacePensierini.length === 0) {
        addLogMessage("WARNING", "Nessun pensierino da esportare")
        return false
    }

    // Qui dovremmo implementare l'esportazione effettiva
    console.log("Esportazione pensierini:", workspacePensierini.length, "elementi")
    addLogMessage("INFO", "Esportazione pensierini avviata")
    return true
}

function clearWorkspacePensierini(workspacePensierini, addLogMessage) {
    workspacePensierini.length = 0
    addLogMessage("INFO", "Tutti i pensierini dell'area di lavoro sono stati eliminati")
}