// ai_functions.js
// Funzioni JavaScript per la gestione dell'AI e Ollama

function sendToAI(mainEditor, selectedModel, aiResultsList, addLogMessage, ollamaBridge) {
    console.log("🔍 QML: sendToAI chiamata")
    console.log("🔍 QML: Testo:", mainEditor.text.substring(0, 50) + "...")
    console.log("🔍 QML: Modello selezionato:", selectedModel)

    if (mainEditor.text.trim() !== "") {
        addLogMessage("INFO", "Invio prompt AI: " + mainEditor.text.substring(0, 30) + "...")

        // Add to AI results list
        var preview = mainEditor.text.length > 50 ? mainEditor.text.substring(0, 47) + "..." : mainEditor.text
        aiResultsList.model.append({
            "preview": preview,
            "fullText": mainEditor.text,
            "response": "Elaborazione in corso...",
            "timestamp": new Date().toLocaleString()
        })

        // Integrazione con Ollama tramite bridge
        if (typeof ollamaBridge !== "undefined") {
            console.log("🔍 QML: Bridge disponibile, invio prompt")
            ollamaBridge.sendPrompt(mainEditor.text, selectedModel)
        } else {
            console.log("🔍 QML: Bridge non disponibile, uso simulazione")
            addLogMessage("WARNING", "Bridge AI non disponibile, uso simulazione")
            // Fallback alla simulazione se il bridge non è disponibile
            simulateAIResponse(mainEditor.text, selectedModel, aiResultsList)
        }
    } else {
        console.log("🔍 QML: Testo vuoto, nessuna azione")
        addLogMessage("WARNING", "Tentativo di invio prompt vuoto")
    }
}

function simulateAIResponse(prompt, selectedModel, aiResultsList) {
    // Simulate AI response - fallback quando il bridge non è disponibile
    var response = "Questa è una risposta simulata dall'AI per il prompt: '" + prompt + "'. In un'implementazione reale, questa risposta verrebbe generata dal modello " + selectedModel + " tramite Ollama."

    // Update the last item in the list
    if (aiResultsList.model.count > 0) {
        var lastIndex = aiResultsList.model.count - 1
        aiResultsList.model.setProperty(lastIndex, "response", response)
    }
}

function selectFirstModel(availableModels, aiModelCombo) {
    if (availableModels.length > 0) {
        return availableModels[0]
    }
    return "llama2:7b"
}

function handleResponseReceived(prompt, response, aiResultsList, addLogMessage) {
    console.log("🔍 QML: Segnale responseReceived ricevuto")
    console.log("🔍 QML: Prompt:", prompt.substring(0, 50) + "...")
    console.log("🔍 QML: Lunghezza risposta:", response.length)

    addLogMessage("INFO", "Risposta AI ricevuta per prompt: " + prompt.substring(0, 30) + "...")

    // Trova l'elemento corrispondente e aggiorna la risposta
    for (var i = 0; i < aiResultsList.model.count; i++) {
        var item = aiResultsList.model.get(i)
        if (item.fullText === prompt && item.response === "Elaborazione in corso...") {
            console.log("🔍 QML: Aggiornamento risposta per elemento", i)
            aiResultsList.model.setProperty(i, "response", response)
            break
        }
    }
}

function handleErrorOccurred(error, aiResultsList, addLogMessage) {
    console.log("🔍 QML: Segnale errorOccurred ricevuto:", error)
    addLogMessage("ERROR", "Errore AI: " + error)

    // Mostra l'errore nell'ultimo elemento
    if (aiResultsList.model.count > 0) {
        var lastIndex = aiResultsList.model.count - 1
        aiResultsList.model.setProperty(lastIndex, "response", "Errore: " + error)
    }
}

function handleModelsLoaded(models, addLogMessage) {
    console.log("🔍 QML: Modelli caricati:", models.length)
    console.log("🔍 QML: Lista modelli:", models)

    addLogMessage("INFO", "Caricati " + models.length + " modelli AI disponibili")

    return models
}

function handleStatusChanged(status, addLogMessage) {
    console.log("🔍 QML: Stato cambiato:", status)
    addLogMessage("INFO", "Stato sistema: " + status)
}