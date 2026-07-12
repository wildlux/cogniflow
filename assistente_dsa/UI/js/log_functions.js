// log_functions.js
// Funzioni JavaScript per la gestione dei log

var logMessages = []  // Array per memorizzare i messaggi di log

function toggleLogMessages(showLogMessages, addLogMessage) {
    if (showLogMessages) {
        console.log("🔍 Log Messages: Attivati - Verranno mostrati errori e warning")
        addLogMessage("INFO", "Sistema di log attivato - Verranno mostrati errori e warning")
    } else {
        console.log("🔍 Log Messages: Disattivati - Messaggi nascosti")
        addLogMessage("INFO", "Sistema di log disattivato")
    }
}

function addLogMessage(level, message) {
    var timestamp = new Date().toLocaleTimeString()
    var logEntry = "[" + timestamp + "] " + level + ": " + message
    logMessages.push(logEntry)

    // Mantieni solo gli ultimi 100 messaggi
    if (logMessages.length > 100) {
        logMessages.shift()
    }

    return logEntry
}

function getLogMessages(showLogMessages) {
    if (logMessages.length === 0) {
        return "Nessun messaggio di log disponibile.\nI messaggi verranno mostrati qui quando si verificano errori o warning."
    }
    if (!showLogMessages) {
        return "Messaggi log disattivati.\nUsa il menu Operazioni > Mostra Messaggi Log per attivarli."
    }
    return logMessages.join("\n")
}

function clearLogMessages(showLogMessages) {
    logMessages = []
    return getLogMessages(showLogMessages)
}

function handleLogMessage(level, message, addLogMessage) {
    console.log("🔍 QML: Messaggio di log ricevuto:", level, message)
    addLogMessage(level, message)
}