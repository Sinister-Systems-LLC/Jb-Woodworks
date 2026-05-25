/* Author: RKOJ-ELENO :: 2026-05-24
 * Minimal Calamares slideshow QML — single static image.
 * Operator wanted "everything has our branding" + "install all in one full auto",
 * so the slideshow is intentionally one static frame of the Sinister mark.
 * Upgrade path: rotate through 3-5 PNG frames when Gemini credits are refilled.
 */
import QtQuick 2.5
import calamares.slideshow 1.0

Presentation {
    id: presentation

    function nextSlide() { /* single-frame slideshow */ }

    Timer {
        interval: 60000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.nextSlide()
    }

    Slide {
        Image {
            id: background
            source: "show.svg"
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
        }
        Text {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottomMargin: 18
            text: qsTr("Installing Sinister OS")
            color: "#e9d5ff"
            font.pixelSize: 16
            font.letterSpacing: 1.2
        }
    }
}
