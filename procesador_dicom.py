import os
import pydicom
import numpy as np
import pandas as pd
import cv2


class ProcesadorDICOM:
    def __init__(self, directorio_entrada, directorio_salida="output"):
        self.directorio_entrada = directorio_entrada
        self.directorio_salida = directorio_salida
        self.archivos = []
        self.metadatos = []
        os.makedirs(self.directorio_salida, exist_ok=True)

    # -------------------------------------------------------------------------
    # 1. Carga de archivos
    # -------------------------------------------------------------------------
    def cargar_archivos(self):
        """Escanea el directorio y carga todos los archivos DICOM válidos."""
        for raiz, _, ficheros in os.walk(self.directorio_entrada):
            for fichero in ficheros:
                ruta = os.path.join(raiz, fichero)
                try:
                    ds = pydicom.dcmread(ruta)
                    self.archivos.append((ruta, ds))
                except Exception:
                    # No es un DICOM válido, se ignora
                    pass

        print(f"[✓] Archivos DICOM cargados: {len(self.archivos)}")

    # -------------------------------------------------------------------------
    # 2. Extracción de metadatos
    # -------------------------------------------------------------------------
    def _get_tag(self, ds, tag, default="N/A"):
        """Extrae un tag del dataset; retorna default si no existe."""
        try:
            valor = getattr(ds, tag)
            return str(valor) if valor is not None else default
        except AttributeError:
            return default

    def extraer_metadatos(self):
        """Extrae los tags DICOM relevantes de cada archivo."""
        for ruta, ds in self.archivos:
            fila = {
                "Archivo": os.path.basename(ruta),
                "PatientID": self._get_tag(ds, "PatientID"),
                "PatientName": self._get_tag(ds, "PatientName"),
                "StudyInstanceUID": self._get_tag(ds, "StudyInstanceUID"),
                "StudyDescription": self._get_tag(ds, "StudyDescription"),
                "StudyDate": self._get_tag(ds, "StudyDate"),
                "Modality": self._get_tag(ds, "Modality"),
                "Rows": self._get_tag(ds, "Rows"),
                "Columns": self._get_tag(ds, "Columns"),
            }
            self.metadatos.append(fila)

        print(f"[✓] Metadatos extraídos de {len(self.metadatos)} archivos")

    # -------------------------------------------------------------------------
    # 3. DataFrame + análisis NumPy
    # -------------------------------------------------------------------------
    def construir_dataframe(self):
        """Construye el DataFrame y añade la columna de intensidad promedio."""
        self.df = pd.DataFrame(self.metadatos)

        intensidades = []
        for _, ds in self.archivos:
            try:
                arr = ds.pixel_array.astype(np.float64)
                intensidades.append(round(arr.mean(), 4))
            except Exception:
                intensidades.append(None)

        self.df["IntensidadPromedio"] = intensidades
        print("[✓] DataFrame construido con IntensidadPromedio")
        return self.df

    # -------------------------------------------------------------------------
    # 4. Procesamiento con OpenCV
    # -------------------------------------------------------------------------
    def _normalizar(self, arr):
        """Escala el arreglo de píxeles a uint8 [0, 255]."""
        arr = arr.astype(np.float64)
        minv, maxv = arr.min(), arr.max()
        if maxv == minv:
            return np.zeros(arr.shape, dtype=np.uint8)
        return ((arr - minv) / (maxv - minv) * 255).astype(np.uint8)

    def procesar_imagenes(self):
        """
        Para cada imagen DICOM:
          - Normaliza a 8 bits
          - Ecualiza el histograma (mejora contraste)
          - Detecta bordes con Canny (umbral bajo=50, alto=150)
          - Guarda los resultados en el directorio de salida
        """
        procesadas = 0
        for ruta, ds in self.archivos:
            try:
                arr = ds.pixel_array

                # Manejo de imágenes multiframe (ej: CT con slices)
                if arr.ndim == 3:
                    arr = arr[0]

                nombre_base = os.path.splitext(os.path.basename(ruta))[0]

                # Normalización
                img_norm = self._normalizar(arr)

                # Ecualización del histograma
                img_ecualizada = cv2.equalizeHist(img_norm)
                cv2.imwrite(
                    os.path.join(self.directorio_salida, f"{nombre_base}_ecualizada.png"),
                    img_ecualizada,
                )

                # Detección de bordes con Canny
                # Umbral bajo=50: captura bordes débiles relevantes en tejidos
                # Umbral alto=150: filtra ruido manteniendo bordes estructurales
                img_bordes = cv2.Canny(img_ecualizada, 50, 150)
                cv2.imwrite(
                    os.path.join(self.directorio_salida, f"{nombre_base}_bordes.png"),
                    img_bordes,
                )

                procesadas += 1

            except Exception:
                # Archivos sin pixel_array (SR, PR, etc.)
                pass

        print(f"[✓] Imágenes procesadas y guardadas: {procesadas}")

    # -------------------------------------------------------------------------
    # 5. Exportar metadatos a CSV
    # -------------------------------------------------------------------------
    def exportar_csv(self, nombre="metadatos_dicom.csv"):
        ruta_csv = os.path.join(self.directorio_salida, nombre)
        self.df.to_csv(ruta_csv, index=False)
        print(f"[✓] Metadatos exportados a: {ruta_csv}")

    # -------------------------------------------------------------------------
    # Pipeline completo
    # -------------------------------------------------------------------------
    def ejecutar(self):
        print("\n=== Iniciando procesamiento DICOM ===\n")
        self.cargar_archivos()
        self.extraer_metadatos()
        df = self.construir_dataframe()
        self.procesar_imagenes()
        self.exportar_csv()
        print("\n=== Procesamiento completado ===\n")
        print(df.to_string(index=False))
        return df


# -----------------------------------------------------------------------------
# Punto de entrada
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    directorio = sys.argv[1] if len(sys.argv) > 1 else "dicom_files"
    procesador = ProcesadorDICOM(
        directorio_entrada=directorio,
        directorio_salida="output",
    )
    procesador.ejecutar()
