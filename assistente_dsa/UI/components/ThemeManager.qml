// ThemeManager.qml
// Componente per la gestione dei temi dell'applicazione - Ottimizzato per Qt Design Studio

import QtQuick 6.2
import QtQuick.Controls 6.2

Item {
    id: themeManager

    // ===== DESIGNER PROPERTIES =====
    // Queste proprietà sono esposte al designer per una facile manipolazione

    // Tema corrente (0-9)
    property int currentTheme: 0

    // ===== THEME COLORS =====
    // Proprietà calcolate per il tema corrente - il designer può vedere questi valori
    readonly property color primaryColor: getThemeColor("primaryColor")
    readonly property color secondaryColor: getThemeColor("secondaryColor")
    readonly property color successColor: getThemeColor("successColor")
    readonly property color errorColor: getThemeColor("errorColor")
    readonly property color backgroundColor: getThemeColor("backgroundColor")
    readonly property color textColor: getThemeColor("textColor")

    // ===== DESIGNER ALIASES =====
    // Alias per permettere al designer di modificare colori specifici
    property alias primaryColorOverride: themeManager.primaryColor
    property alias backgroundColorOverride: themeManager.backgroundColor
    property alias textColorOverride: themeManager.textColor

    // ===== THEME DEFINITIONS =====
    // Definizione dei temi - ottimizzata per il designer
    QtObject {
        id: themeDefinitions

        // Tema 0: Classico (Blu)
        readonly property var classicTheme: ({
            name: "Classico",
            primaryColor: "#4a90e2",
            secondaryColor: "#f39c12",
            successColor: "#27ae60",
            errorColor: "#e74c3c",
            backgroundColor: "#f8f9fa",
            textColor: "#000000"
        })

        // Tema 1: Scuro
        readonly property var darkTheme: ({
            name: "Scuro",
            primaryColor: "#6c757d",
            secondaryColor: "#495057",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#343a40",
            textColor: "#ffffff"
        })

        // Tema 2: Chiaro
        readonly property var lightTheme: ({
            name: "Chiaro",
            primaryColor: "#007bff",
            secondaryColor: "#6c757d",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#ffffff",
            textColor: "#000000"
        })

        // Tema 3: Natura (Verdi)
        readonly property var natureTheme: ({
            name: "Natura",
            primaryColor: "#28a745",
            secondaryColor: "#20c997",
            successColor: "#17a2b8",
            errorColor: "#dc3545",
            backgroundColor: "#f8fff8",
            textColor: "#155724"
        })

        // Tema 4: Sunset (Arancione/Rosso)
        readonly property var sunsetTheme: ({
            name: "Sunset",
            primaryColor: "#fd7e14",
            secondaryColor: "#e83e8c",
            successColor: "#ffc107",
            errorColor: "#dc3545",
            backgroundColor: "#fff8f3",
            textColor: "#721c24"
        })

        // Tema 5: Oceano (Blu/Azzurro)
        readonly property var oceanTheme: ({
            name: "Oceano",
            primaryColor: "#17a2b8",
            secondaryColor: "#6f42c1",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#f0f8ff",
            textColor: "#0c5460"
        })

        // Tema 6: Lavanda (Viola)
        readonly property var lavenderTheme: ({
            name: "Lavanda",
            primaryColor: "#6f42c1",
            secondaryColor: "#e83e8c",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#faf5ff",
            textColor: "#4b0082"
        })

        // Tema 7: Moderno (Grigio/Nero)
        readonly property var modernTheme: ({
            name: "Moderno",
            primaryColor: "#000000",
            secondaryColor: "#6c757d",
            successColor: "#28a745",
            errorColor: "#dc3545",
            backgroundColor: "#f8f9fa",
            textColor: "#000000"
        })

        // Tema 8: Arcobaleno (Colori Vivaci)
        readonly property var rainbowTheme: ({
            name: "Arcobaleno",
            primaryColor: "#ff6b6b",
            secondaryColor: "#4ecdc4",
            successColor: "#45b7d1",
            errorColor: "#f9ca24",
            backgroundColor: "#fff5f5",
            textColor: "#2d3436"
        })

        // Tema 9: Minimal (Bianco/Nero)
        readonly property var minimalTheme: ({
            name: "Minimal",
            primaryColor: "#000000",
            secondaryColor: "#ffffff",
            successColor: "#000000",
            errorColor: "#ff0000",
            backgroundColor: "#ffffff",
            textColor: "#000000"
        })
    }

    // Array dei temi per accesso programmatico
    readonly property var themes: [
        themeDefinitions.classicTheme,
        themeDefinitions.darkTheme,
        themeDefinitions.lightTheme,
        themeDefinitions.natureTheme,
        themeDefinitions.sunsetTheme,
        themeDefinitions.oceanTheme,
        themeDefinitions.lavenderTheme,
        themeDefinitions.modernTheme,
        themeDefinitions.rainbowTheme,
        themeDefinitions.minimalTheme
    ]

    // Nomi dei temi per il ComboBox - ottimizzati per il designer
    readonly property var themeNames: [
        "🔵 Classico (Blu)",
        "⚫ Scuro",
        "⚪ Chiaro",
        "🌿 Natura (Verde)",
        "🌅 Sunset (Arancione)",
        "🌊 Oceano (Azzurro)",
        "💜 Lavanda (Viola)",
        "🎯 Moderno (Nero)",
        "🌈 Arcobaleno",
        "🎨 Minimal (Bianco/Nero)"
    ]

    // ===== DESIGNER FUNCTIONS =====
    // Funzione helper per ottenere colori del tema corrente
    function getThemeColor(colorName) {
        if (currentTheme >= 0 && currentTheme < themes.length) {
            return themes[currentTheme][colorName] || "#000000"
        }
        return "#000000"
    }

    // Funzione per cambiare tema - ottimizzata per il designer
    function setTheme(index) {
        if (index >= 0 && index < themes.length) {
            currentTheme = index
        }
    }

    // Funzione per tema casuale
    function randomTheme() {
        currentTheme = Math.floor(Math.random() * themes.length)
    }

    // Funzione per resettare al tema classico
    function resetTheme() {
        currentTheme = 0
    }

    // ===== DESIGNER STATES =====
    // Stati per il designer
    states: [
        State {
            name: "classic"
            PropertyChanges { target: themeManager; currentTheme: 0 }
        },
        State {
            name: "dark"
            PropertyChanges { target: themeManager; currentTheme: 1 }
        },
        State {
            name: "light"
            PropertyChanges { target: themeManager; currentTheme: 2 }
        }
    ]

    // ===== DESIGNER METADATA =====
    // Metadata per Qt Design Studio
    Component.onCompleted: {
        // Inizializzazione del tema
        console.log("ThemeManager initialized with theme:", themes[currentTheme].name)
    }
}