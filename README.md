# Taller-3--Info2-G2-Meilin_Almanza
*Estudiante:** Meilin Sofia Almanza Moreno
*Grupo:** 2

---

## Descripción del proyecto

Este proyecto implementa un procesador de archivos DICOM en Python. La clase principal `ProcesadorDICOM` automatiza la lectura de estudios médicos, extrae sus metadatos, calcula la intensidad promedio de cada imagen con NumPy, y aplica procesamiento básico con OpenCV (ecualización de histograma y detección de bordes con Canny). Los resultados se almacenan en un DataFrame de Pandas exportado a CSV, junto con las imágenes procesadas en formato PNG.

---

## Archivos del repositorio

- `procesador_dicom.py` — script principal con la clase `ProcesadorDICOM`
- `requirements.txt` — dependencias del proyecto
- `README.md` — este archivo
- `output/` — carpeta generada al correr el script con imágenes procesadas y CSV de metadatos

---

## Cómo ejecutar

```bash
# Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar con la carpeta que contiene los archivos DICOM
python procesador_dicom.py ruta/al/directorio_dicom
```

Para obtener archivos DICOM de prueba, se puede usar directamente la librería `pydicom`:

```python
import pydicom, shutil, os
from pydicom.data import get_testdata_file

os.makedirs("dicom_files", exist_ok=True)
for nombre in ["CT_small.dcm", "MR_small.dcm", "rtdose.dcm"]:
    shutil.copy(get_testdata_file(nombre), "dicom_files/")
```

---

## DICOM vs HL7: interoperabilidad en salud

DICOM y HL7 son los dos estándares más importantes para la interoperabilidad en salud, pero operan en capas distintas.

**DICOM** fue diseñado específicamente para imágenes médicas. No solo define el formato del archivo (que incluye la imagen y sus metadatos clínicos en un solo objeto), sino también los protocolos de red para transferir esas imágenes entre equipos como tomógrafos, resonadores y sistemas PACS.

**HL7** (especialmente en su versión FHIR) tiene un alcance más amplio: se enfoca en el intercambio de información clínica general entre sistemas de salud, como historias clínicas electrónicas, resultados de laboratorio, órdenes médicas y datos administrativos del paciente. No está pensado para transportar imágenes.

La diferencia conceptual clave es que DICOM es un estándar orientado al objeto-imagen (el archivo ya trae todo lo necesario para interpretarla), mientras que HL7/FHIR está orientado a mensajes y recursos clínicos estructurados. En la práctica ambos coexisten: un sistema hospitalario puede usar HL7 para enviar la orden de un estudio y DICOM para transferir las imágenes resultantes.

---

## Ecualización de histograma y Canny en imágenes médicas

### Ventajas

La **ecualización de histograma** redistribuye las intensidades de los píxeles para mejorar el contraste global. En radiografías con bajo contraste o imágenes subexpuestas puede hacer visibles estructuras que de otro modo serían difíciles de distinguir. Es rápida, no requiere parámetros y funciona bien como normalización antes de otros algoritmos.

El **detector de bordes de Canny** combina suavizado gaussiano, cálculo del gradiente y supresión de no-máximos, lo que reduce el ruido y produce bordes delgados y bien definidos. Puede ser útil para segmentar estructuras como huesos, márgenes de órganos o nódulos como etapa inicial de un pipeline de análisis.

### Limitaciones

La ecualización de histograma global puede sobrealzar el ruido y distorsionar regiones que ya tenían buen contraste. En tomografías puede hacer que artefactos de reconstrucción se vean como estructuras reales. Para uso clínico, CLAHE (ecualización adaptativa por tiles) suele ser más apropiada.

Canny también tiene limitaciones: los umbrales son sensibles al tipo de imagen y no hay valores universales. En imágenes con ruido (resonancias con artefactos de movimiento) puede generar bordes falsos. Además, solo detecta bordes y no los interpreta, por lo que sus resultados necesitan contexto clínico para ser útiles.

Ambas técnicas son valiosas como preprocesamiento exploratorio, pero no deberían usarse aisladamente para decisiones diagnósticas.

---

## Dificultades encontradas e importancia de Python

La principal dificultad fue manejar la heterogeneidad de los archivos DICOM: no todos tienen los mismos tags disponibles (muchos pasan por anonimización que elimina datos del paciente), y varios archivos no contienen pixel data sino metadatos de otro tipo (SR, PR). Fue necesario usar bloques `try/except` en casi todo el código para que el script fuera robusto.

Otro punto fue la normalización: los arreglos de píxeles en DICOM suelen estar en 12 o 16 bits y OpenCV trabaja con uint8, así que fue necesario escalar correctamente a [0, 255] antes de cualquier procesamiento.

Python con `pydicom`, `NumPy`, `Pandas` y `OpenCV` resultó ser un stack muy conveniente: permite acceder a datos clínicos crudos, procesarlos matemáticamente y aplicar visión por computador en pocas líneas, lo que sería mucho más complejo con herramientas de bajo nivel.
