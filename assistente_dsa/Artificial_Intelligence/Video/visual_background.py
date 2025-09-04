# visual_background.py

import cv2
import logging
import numpy as np
import math
from PyQt6.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QImage, QPixmap

class VideoThread(QThread):
    """
    Thread per la cattura e l'elaborazione del flusso video dalla webcam.
    """
    change_pixmap_signal = pyqtSignal(QPixmap)  # Invia QPixmap invece di dati raw per efficienza
    status_signal = pyqtSignal(str)

    def __init__(self, main_window=None):
        super().__init__()
        self._run_flag = True
        self.face_detection_enabled = False
        self.hand_detection_enabled = False
        self.gesture_recognition_enabled = False
        self.facial_expression_enabled = False
        self.main_window = main_window

        # Carica i classificatori Haar per il rilevamento
        try:
            import cv2.data
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                logging.warning("File Haar cascade per il rilevamento facciale non trovato. Rilevamento facciale disabilitato.")
                self.face_cascade = None
        except Exception as e:
            logging.error(f"Errore nel caricamento del cascade Haar: {e}")
            self.face_cascade = None

        # Per le mani, usiamo un approccio alternativo basato sulla pelle
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        # Parametri per il riconoscimento dei gesti
        self.prev_hand_positions = []
        self.gesture_history = []
        self.selected_widget = None
        self.drag_start_time: float = 0.0
        self.is_dragging = False
        self.drag_timer = 0
        self.DRAG_THRESHOLD = 6.0  # 6 secondi per iniziare il trascinamento

        # Parametri per il riconoscimento delle espressioni facciali
        self.prev_face_positions = []
        self.expression_history = []

        # Parametri per il riconoscimento avanzato delle mani
        self.hand_tracking = {
            'left': {'position': None, 'fingers': 0, 'gesture': 'unknown', 'confidence': 0},
            'right': {'position': None, 'fingers': 0, 'gesture': 'unknown', 'confidence': 0}
        }
        self.active_inputs = set()  # Traccia dispositivi attivi (mani + mouse)

    def run(self):
        """Metodo principale del thread."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.status_signal.emit("Errore: Impossibile aprire la webcam.")
            self._run_flag = False
            return

        self.status_signal.emit("Webcam avviata. Caricamento...")

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                # ==========================================================
                # Modifica qui per invertire orizzontalmente l'immagine
                # Il valore 1 indica l'inversione orizzontale.
                # ==========================================================
                frame = cv2.flip(frame, 1)

                # ==========================================================
                # Logica di rilevamento faccia, mani, gesti ed espressioni
                # ==========================================================

                # Mostra sempre lo stato dei rilevamenti
                status_text = ""
                if self.face_detection_enabled:
                    status_text += "Faccia: ON  "
                else:
                    status_text += "Faccia: OFF  "

                if self.hand_detection_enabled:
                    status_text += "Mani: ON  "
                else:
                    status_text += "Mani: OFF  "

                if self.gesture_recognition_enabled:
                    status_text += "Gesti: ON  "
                else:
                    status_text += "Gesti: OFF  "

                if self.facial_expression_enabled:
                    status_text += "Espressioni: ON"
                else:
                    status_text += "Espressioni: OFF"

                cv2.putText(frame, status_text, (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                # Applica i rilevamenti nell'ordine corretto
                if self.face_detection_enabled:
                    frame = self.detect_faces(frame)

                if self.hand_detection_enabled:
                    frame = self.detect_hands(frame)

                if self.gesture_recognition_enabled:
                    frame = self.detect_hand_gestures(frame)

                if self.facial_expression_enabled:
                    frame = self.detect_facial_expressions(frame)

                # Converti il frame in QPixmap per efficienza
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = rgb_image.shape[:2]
                # Converti in bytes per QImage
                bytes_per_line = 3 * w
                # Converti esplicitamente in bytes
                image_bytes = bytes(rgb_image.tobytes())
                q_image = QImage(image_bytes, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                # Invia QPixmap invece di dati raw per ridurre uso memoria
                self.change_pixmap_signal.emit(pixmap)
            else:
                self.status_signal.emit("Errore di lettura del frame dalla webcam.")
                break

        # Rilascia la webcam quando il thread si ferma
        self.cap.release()
        logging.info("VideoThread terminato e webcam rilasciata.")

    def detect_faces(self, frame):
        """Rileva le facce nel frame e disegna rettangoli."""
        if self.face_cascade is None:
            # Se il cascade non è disponibile, mostra un messaggio
            cv2.putText(frame, 'Rilevamento faccia non disponibile', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Parametri più sensibili per il rilevamento facciale
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,  # Ridotto per più precisione
            minNeighbors=3,    # Ridotto per più rilevamenti
            minSize=(30, 30),  # Dimensione minima più piccola
            maxSize=(300, 300) # Dimensione massima
        )

        # Mostra sempre lo stato del rilevamento
        if len(faces) > 0:
            cv2.putText(frame, f'Faccia rilevata: {len(faces)}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, 'Nessuna faccia rilevata', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 3)  # Rettangolo più spesso
            cv2.putText(frame, 'Faccia', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

        return frame

    def detect_hand_gestures(self, frame):
        """Rileva i gesti delle mani avanzati con riconoscimento destra/sinistra e dita."""
        if not self.gesture_recognition_enabled:
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

        # Operazioni morfologiche avanzate
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Trova i contorni con approssimazione migliore
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

        detected_hands = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 5000 < area < 50000:  # Range più preciso per le mani
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0

                if 0.4 < aspect_ratio < 2.5:  # Range più ampio per diverse orientamenti
                    # Analisi avanzata della mano
                    hand_info = self.analyze_hand_advanced(contour, x, y, w, h, frame.shape[1])

                    if hand_info['confidence'] > 0.3:  # Solo mani con buona confidenza
                        detected_hands.append((x, y, w, h, hand_info))

                        # Colore diverso per mano destra e sinistra
                        if hand_info['hand_type'] == 'right':
                            color = (0, 255, 0)  # Verde per destra
                        else:
                            color = (255, 0, 255)  # Magenta per sinistra

                        # Disegna rettangolo e informazioni
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)

                        # Info sulla mano
                        info_text = f"{hand_info['hand_type'].upper()}: {hand_info['fingers']} dita, {hand_info['gesture']}"
                        cv2.putText(frame, info_text, (x, y-15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                        # Info sulle dita individuali
                        finger_text = f"Pollice:{'ON' if hand_info['thumb'] else 'OFF'} Indice:{'ON' if hand_info['index'] else 'OFF'}"
                        cv2.putText(frame, finger_text, (x, y+h+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

                        # Gestisci l'interazione con l'interfaccia
                        frame = self.handle_advanced_hand_interaction(frame, x, y, w, h, hand_info)

        # Aggiorna il tracking delle mani
        self.update_hand_tracking(detected_hands)

        # Mostra statistiche
        self.display_hand_statistics(frame, detected_hands)

        return frame

    def detect_hands(self, frame):
        """Rileva le mani nel frame usando il colore della pelle."""
        if not self.hand_detection_enabled:
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)

        # Operazioni morfologiche per migliorare la maschera
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Trova i contorni nell'immagine binaria
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        hand_count = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 3000:  # Soglia ridotta per più rilevamenti
                x, y, w, h = cv2.boundingRect(contour)
                # Filtra per proporzioni ragionevoli (mani non troppo strette o larghe)
                aspect_ratio = w / h if h > 0 else 0
                if 0.5 < aspect_ratio < 2.0:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Verde per mani base
                    cv2.putText(frame, 'Mano', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                    hand_count += 1

        # Mostra lo stato del riconoscimento mani
        if hand_count > 0:
            cv2.putText(frame, f'Mani rilevate: {hand_count}', (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            cv2.putText(frame, 'Nessuna mano rilevata', (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return frame

    def analyze_hand_shape(self, contour, x, y, w, h):
        """Analizza la forma del contorno per determinare il gesto della mano."""
        # Calcola la convessità
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        if hull_area > 0:
            solidity = contour_area / hull_area
        else:
            solidity = 0

        # Calcola il perimetro e la compattezza
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            compactness = (4 * math.pi * contour_area) / (perimeter * perimeter)
        else:
            compactness = 0

        # Calcola l'aspetto ratio
        aspect_ratio = w / h if h > 0 else 0

        # Calcola i difetti di convessità per contare le dita
        hull_indices = cv2.convexHull(contour, returnPoints=False)

        # Verifica che gli indici siano validi e in ordine monotono
        defects = None
        if hull_indices is not None and len(hull_indices) > 0:
            try:
                # Verifica che gli indici siano in ordine crescente
                if np.all(hull_indices[:-1] <= hull_indices[1:]):
                    defects = cv2.convexityDefects(contour, hull_indices)
                else:
                    # Se non sono in ordine, riordina
                    sorted_indices = np.sort(hull_indices.flatten())
                    defects = cv2.convexityDefects(contour, sorted_indices.reshape(-1, 1))
            except cv2.error as e:
                # Se si verifica un errore, logga e continua senza difetti
                print(f"Errore in convexityDefects (analyze_hand_shape): {e}")
                defects = None

        finger_count = 0
        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                # Calcola la distanza dal punto lontano al contorno
                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)

                # Usa la formula di Erone per calcolare l'area
                s = (a + b + c) / 2
                area = math.sqrt(max(0, s * (s - a) * (s - b) * (s - c)))

                # Calcola la distanza dal punto lontano
                distance = (2 * area) / a if a > 0 else 0

                # Conta le dita basandosi sulla profondità dei difetti
                if distance > 15:  # Soglia ridotta per più sensibilità
                    finger_count += 1

        # Algoritmo migliorato per distinguere mano aperta/chiusa
        # Mano chiusa: alta compattezza, bassa solidità, poche dita
        # Mano aperta: bassa compattezza, alta solidità, molte dita

        # Criteri per mano chiusa:
        # - Alta compattezza (forma più circolare)
        # - Bassa solidità (molti spazi vuoti)
        # - Poche dita rilevate
        # - Aspect ratio vicino a 1 (quasi quadrata)

        is_closed_by_compactness = compactness > 0.6
        is_closed_by_solidity = solidity < 0.7
        is_closed_by_fingers = finger_count <= 2
        is_closed_by_aspect = 0.7 < aspect_ratio < 1.4

        # Criteri per mano aperta:
        # - Bassa compattezza (forma allungata)
        # - Alta solidità (poca concavità)
        # - Molte dita rilevate
        is_open_by_compactness = compactness < 0.4
        is_open_by_solidity = solidity > 0.8
        is_open_by_fingers = finger_count >= 3

        # Decisione finale
        if (is_closed_by_compactness and is_closed_by_solidity and is_closed_by_fingers) or \
           (is_closed_by_aspect and is_closed_by_fingers):
            return "Mano Chiusa"
        elif is_open_by_compactness and is_open_by_solidity and is_open_by_fingers:
            return "Mano Aperta"
        else:
            return "Gesto Parziale"

    def detect_facial_expressions(self, frame):
        """Rileva le espressioni facciali usando landmark e geometria."""
        if not self.facial_expression_enabled or self.face_cascade is None:
            return frame

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(30, 30),
            maxSize=(300, 300)
        )

        expression_count = 0
        for (x, y, w, h) in faces:
            # Estrai la regione del volto
            face_roi = gray[y:y+h, x:x+w]

            # Analizza l'espressione usando caratteristiche geometriche
            expression = self.analyze_facial_expression(face_roi, x, y, w, h)

            # Disegna il rettangolo e l'espressione rilevata
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 3)  # Magenta per espressioni
            cv2.putText(frame, f'Espressione: {expression}', (x, y+h+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            expression_count += 1

        # Mostra lo stato del riconoscimento espressioni
        if expression_count > 0:
            cv2.putText(frame, f'Espressioni rilevate: {expression_count}', (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
        else:
            cv2.putText(frame, 'Nessuna espressione rilevata', (10, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        return frame

    def analyze_facial_expression(self, face_roi, x, y, w, h):
        """Analizza l'espressione facciale usando caratteristiche geometriche e texture."""
        if face_roi.size == 0:
            return "Non rilevabile"

        # Converti in scala di grigi se necessario
        if len(face_roi.shape) > 2:
            face_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)

        height, width = face_roi.shape

        # Migliora il contrasto per una migliore analisi
        face_roi = cv2.equalizeHist(face_roi)

        # Dividi il volto in regioni più precise
        eye_region = face_roi[height//5:2*height//5, :]  # Regione occhi
        nose_region = face_roi[2*height//5:3*height//5, :]  # Regione naso
        mouth_region = face_roi[3*height//5:4*height//5, :]  # Regione bocca

        # Calcola statistiche per ogni regione
        eye_mean = np.mean(eye_region)
        eye_std = np.std(eye_region)
        nose_mean = np.mean(nose_region)
        nose_std = np.std(nose_region)
        mouth_mean = np.mean(mouth_region)
        mouth_std = np.std(mouth_region)

        # Calcola i gradienti per rilevare i contorni
        sobelx = cv2.Sobel(face_roi, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(face_roi, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)

        # Analizza la regione della bocca (dove si concentrano le espressioni)
        mouth_gradient = np.mean(gradient_magnitude[3*height//5:4*height//5, :])
        mouth_gradient_std = np.std(gradient_magnitude[3*height//5:4*height//5, :])

        # Calcola l'entropia per misurare la complessità della texture
        def calculate_entropy(region):
            hist = cv2.calcHist([region], [0], None, [256], [0, 256])
            hist = hist / hist.sum()  # Normalizza
            entropy = -np.sum(hist * np.log2(hist + 1e-10))  # Evita log(0)
            return entropy

        eye_entropy = calculate_entropy(eye_region)
        mouth_entropy = calculate_entropy(mouth_region)

        # Algoritmo di classificazione migliorato
        # Sorriso: alta variazione nella regione bocca, luminosità aumentata
        is_smile = (mouth_gradient > 30 and mouth_std > 25 and
                   mouth_entropy > 6.5 and mouth_mean > eye_mean)

        # Triste: bassa variazione, luminosità diminuita nella regione inferiore
        is_sad = (mouth_gradient < 15 and mouth_std < 20 and
                 mouth_mean < eye_mean and mouth_entropy < 6.0)

        # Sorpreso: alta entropia in regione occhi, variazione elevata
        is_surprised = (eye_entropy > 7.0 and eye_std > 30 and
                       mouth_gradient > 25 and mouth_std > 25)

        # Neutro: valori intermedi, bassa variazione
        is_neutral = (15 <= mouth_gradient <= 30 and
                     20 <= mouth_std <= 30 and
                     6.0 <= mouth_entropy <= 7.0)

        # Decisione finale basata sui punteggi
        if is_smile:
            return "Sorriso"
        elif is_sad:
            return "Triste"
        elif is_surprised:
            return "Sorpreso"
        elif is_neutral:
            return "Neutro"
        else:
            return "Neutro"

    def check_hand_interaction(self, frame, hand_x, hand_y, hand_w, hand_h, gesture):
        """Verifica se la mano sta interagendo con elementi dell'interfaccia."""
        if not hasattr(self, 'main_window') or self.main_window is None:
            return frame

        # Coordinate approssimative della colonna A (pensierini)
        # Queste sono stime basate sul layout tipico dell'interfaccia
        column_a_left = 50
        column_a_right = frame.shape[1] // 3
        column_a_top = 100
        column_a_bottom = frame.shape[0] - 100

        # Verifica se la mano è nella colonna A
        hand_center_x = hand_x + hand_w // 2
        hand_center_y = hand_y + hand_h // 2

        is_in_column_a = (column_a_left < hand_center_x < column_a_right and
                         column_a_top < hand_center_y < column_a_bottom)

        if is_in_column_a:
            # Disegna un'indicazione visiva che la mano è nella zona di interazione
            cv2.rectangle(frame, (column_a_left, column_a_top),
                         (column_a_right, column_a_bottom), (0, 255, 255), 2)
            cv2.putText(frame, 'ZONA INTERAZIONE', (column_a_left + 10, column_a_top + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Se la mano è chiusa, inizia il trascinamento
            if gesture == "Mano Chiusa" and not self.is_dragging:
                self.start_dragging()
                cv2.putText(frame, 'TRASCINAMENTO INIZIATO!', (hand_center_x - 100, hand_center_y - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            elif gesture == "Mano Aperta" and self.is_dragging:
                self.stop_dragging()
                cv2.putText(frame, 'TRASCINAMENTO COMPLETATO!', (hand_center_x - 120, hand_center_y - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

    def start_dragging(self):
        """Inizia il processo di trascinamento."""
        import time
        self.is_dragging = True
        self.drag_start_time = time.time()
        logging.info("Iniziato trascinamento con gesto mano chiusa")

    def stop_dragging(self):
        """Termina il processo di trascinamento e simula il drop nell'area centrale."""
        import time
        if self.is_dragging and self.drag_start_time > 0:
            drag_duration = time.time() - self.drag_start_time
            self.is_dragging = False
            self.drag_start_time = 0.0

            # Simula il trascinamento nell'area centrale
            self.simulate_drag_to_center()

            logging.info(f"Trascinamento completato in {drag_duration:.2f} secondi")
        else:
            self.is_dragging = False
            self.drag_start_time = 0.0

    def simulate_drag_to_center(self):
        """Simula il trascinamento di un elemento nell'area centrale."""
        if hasattr(self, 'main_window') and self.main_window:
            try:
                # Trova l'ultimo widget nella colonna A
                widgets = []
                for i in range(self.main_window.draggable_widgets_layout.count()):
                    item = self.main_window.draggable_widgets_layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget:
                            widgets.append(widget)

                if widgets:
                    # Prendi l'ultimo widget
                    last_widget = widgets[-1]
                    text = last_widget.text_label.text()

                    # Aggiungi il testo all'area centrale
                    current_text = self.main_window.work_area_main_text_edit.toPlainText()
                    new_text = current_text + f"\n\n[TRASCINATO]: {text}"
                    self.main_window.work_area_main_text_edit.setText(new_text)

                    # Rimuovi il widget dalla colonna A
                    last_widget.setParent(None)
                    last_widget.deleteLater()

                    logging.info(f"Elemento trascinato con successo: {text}")

            except Exception as e:
                logging.error(f"Errore durante il trascinamento: {e}")

    def analyze_hand_advanced(self, contour, x, y, w, h, frame_width):
        """Analisi avanzata della mano con riconoscimento destra/sinistra e dita individuali."""
        # Calcola il centro della mano
        center_x = x + w // 2

        # Determina se è destra o sinistra basandosi sulla posizione orizzontale
        if center_x < frame_width // 2:
            hand_type = 'left'
        else:
            hand_type = 'right'

        # Analisi della forma per contare le dita
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)

        if hull_area > 0:
            solidity = contour_area / hull_area
        else:
            solidity = 0

        # Calcola i difetti di convessità per le dita
        hull_indices = cv2.convexHull(contour, returnPoints=False)

        # Verifica che gli indici siano validi e in ordine monotono
        defects = None
        if hull_indices is not None and len(hull_indices) > 0:
            try:
                # Verifica che gli indici siano in ordine crescente
                if np.all(hull_indices[:-1] <= hull_indices[1:]):
                    defects = cv2.convexityDefects(contour, hull_indices)
                else:
                    # Se non sono in ordine, riordina
                    sorted_indices = np.sort(hull_indices.flatten())
                    defects = cv2.convexityDefects(contour, sorted_indices.reshape(-1, 1))
            except cv2.error as e:
                # Se si verifica un errore, logga e continua senza difetti
                print(f"Errore in convexityDefects: {e}")
                defects = None

        finger_count = 0
        thumb_detected = False
        index_detected = False

        if defects is not None:
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(contour[s][0])
                end = tuple(contour[e][0])
                far = tuple(contour[f][0])

                # Calcola la profondità del difetto
                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)

                if a > 0:
                    area = math.sqrt(max(0, (s * (s - a) * (s - b) * (s - c))))
                    distance = (2 * area) / a
                else:
                    distance = 0

                # Conta le dita basandosi sulla profondità
                if distance > 20:
                    finger_count += 1

                    # Identifica pollice e indice basandosi sulla posizione
                    if hand_type == 'right':
                        if far[0] > start[0] and far[0] > end[0]:  # Pollice a destra per mano destra
                            thumb_detected = True
                        elif finger_count == 1:  # Primo dito dopo il pollice
                            index_detected = True
                    else:  # Mano sinistra
                        if far[0] < start[0] and far[0] < end[0]:  # Pollice a sinistra per mano sinistra
                            thumb_detected = True
                        elif finger_count == 1:
                            index_detected = True

        # Determina il gesto basato su dita e solidità
        if finger_count >= 4 and solidity > 0.75:
            gesture = "Mano Aperta"
        elif finger_count <= 2 or solidity < 0.65:
            gesture = "Mano Chiusa"
        else:
            gesture = "Gesto Parziale"

        # Calcola la confidenza
        confidence = min(1.0, (finger_count * 0.2) + (solidity * 0.3) + 0.3)

        return {
            'hand_type': hand_type,
            'fingers': finger_count,
            'thumb': thumb_detected,
            'index': index_detected,
            'gesture': gesture,
            'confidence': confidence,
            'solidity': solidity
        }

    def update_hand_tracking(self, detected_hands):
        """Aggiorna il tracking delle mani per il sistema multi-input."""
        # Reset delle posizioni precedenti
        for hand_type in ['left', 'right']:
            self.hand_tracking[hand_type]['position'] = None
            self.hand_tracking[hand_type]['confidence'] = 0

        # Aggiorna con le mani rilevate
        for x, y, w, h, hand_info in detected_hands:
            hand_type = hand_info['hand_type']
            self.hand_tracking[hand_type]['position'] = (x + w//2, y + h//2)
            self.hand_tracking[hand_type]['fingers'] = hand_info['fingers']
            self.hand_tracking[hand_type]['gesture'] = hand_info['gesture']
            self.hand_tracking[hand_type]['confidence'] = hand_info['confidence']

    def display_hand_statistics(self, frame, detected_hands):
        """Mostra le statistiche delle mani rilevate."""
        if detected_hands:
            left_count = sum(1 for _, _, _, _, info in detected_hands if info['hand_type'] == 'left')
            right_count = sum(1 for _, _, _, _, info in detected_hands if info['hand_type'] == 'right')

            stats_text = f"Mani rilevate: SX:{left_count} DX:{right_count}"
            cv2.putText(frame, stats_text, (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
        else:
            cv2.putText(frame, 'Nessuna mano rilevata', (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)

    def handle_advanced_hand_interaction(self, frame, hand_x, hand_y, hand_w, hand_h, hand_info):
        """Gestisce l'interazione avanzata con l'interfaccia usando le mani."""
        if not hasattr(self, 'main_window') or self.main_window is None:
            return frame

        # Coordinate della zona di interazione (colonna A)
        column_a_left = 50
        column_a_right = frame.shape[1] // 3
        column_a_top = 100
        column_a_bottom = frame.shape[0] - 100

        hand_center_x = hand_x + hand_w // 2
        hand_center_y = hand_y + hand_h // 2

        is_in_interaction_zone = (column_a_left < hand_center_x < column_a_right and
                                column_a_top < hand_center_y < column_a_bottom)

        if is_in_interaction_zone:
            # Disegna la zona di interazione
            cv2.rectangle(frame, (column_a_left, column_a_top),
                         (column_a_right, column_a_bottom), (0, 255, 255), 2)
            cv2.putText(frame, 'ZONA INTERAZIONE', (column_a_left + 10, column_a_top + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Gestisci il trascinamento con timer
            if hand_info['gesture'] == "Mano Chiusa":
                if not self.is_dragging:
                    import time
                    current_time = time.time()

                    if self.drag_start_time == 0.0:
                        self.drag_start_time = current_time
                        self.drag_timer = 0
                    else:
                        self.drag_timer = current_time - self.drag_start_time

                    if self.drag_timer >= self.DRAG_THRESHOLD:
                        self.start_dragging()
                        cv2.putText(frame, 'TRASCINAMENTO INIZIATO!', (hand_center_x - 100, hand_center_y - 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        remaining = int(self.DRAG_THRESHOLD - self.drag_timer)
                        cv2.putText(frame, f'Mantieni chiusa per {remaining}s', (hand_center_x - 80, hand_center_y - 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                if self.is_dragging:
                    self.stop_dragging()
                    cv2.putText(frame, 'TRASCINAMENTO COMPLETATO!', (hand_center_x - 120, hand_center_y - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                else:
                    self.drag_start_time = 0.0
                    self.drag_timer = 0

        return frame

    def stop(self):
        """Termina il thread in modo sicuro."""
        self._run_flag = False
        self.wait()
