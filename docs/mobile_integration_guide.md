# Guía de Conexión Móvil para Mr. Rose (Flutter / React Native / Android)

Esta guía describe cómo conectar tu aplicación móvil con el backend de **Mr. Rose MCP** para enviar fotografías tomadas con la cámara del smartphone y recibir diagnósticos fitopatológicos interactivos.

---

## 🌐 Endpoints Disponibles

### 1. Diagnosticar Fotografía (Recomendado)
* **Método:** `POST`
* **Ruta:** `/api/v1/diagnose/file`
* **Tipo:** `multipart/form-data`
* **Campos:**
  * `file`: Archivo binario de la foto (JPEG/PNG).
  * `context_notes` *(opcional)*: Notas adicionales del agricultor (ej: *"Invernadero bloque 3, Cotopaxi, riego por aspersión"*).

---

## 📲 Ejemplo de Integración en Flutter (Dart)

```dart
import 'dart:io';
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<Map<String, dynamic>> diagnosticarRosa(File imageFile, {String? notas}) async {
  // En local con emulador Android usa: http://10.0.2.2:8000
  // En dispositivo físico en la misma red WiFi usa: http://TU_IP_LOCAL:8000
  // En producción usa la URL de Render/Cloud: https://mrrose-mcp.onrender.com
  final uri = Uri.parse('http://10.0.2.2:8000/api/v1/diagnose/file');

  var request = http.MultipartRequest('POST', uri);
  request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
  
  if (notas != null) {
    request.fields['context_notes'] = notas;
  }

  var streamedResponse = await request.send();
  var response = await http.Response.fromStream(streamedResponse);

  if (response.statusCode == 200) {
    return jsonDecode(utf8.decode(response.bodyBytes));
  } else {
    throw Exception('Error al diagnosticar: ${response.statusCode}');
  }
}
```

---

## 📲 Ejemplo de Integración en React Native

```javascript
import axios from 'axios';

const diagnosticarRosa = async (photoUri, notas = '') => {
  const formData = new FormData();
  formData.append('file', {
    uri: photoUri,
    type: 'image/jpeg',
    name: 'foto_rosa.jpg',
  });
  if (notas) {
    formData.append('context_notes', notas);
  }

  const response = await axios.post('http://TU_IP_LOCAL:8000/api/v1/diagnose/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};
```

---

## 📋 Estructura de la Respuesta que Recibe la App Móvil

```json
{
  "diagnostico_probable": "mancha_negra",
  "nombre_comun": "Mancha negra de la rosa",
  "nombre_cientifico": "Diplocarpon rosae",
  "confianza": 0.95,
  "organos_afectados": ["hoja"],
  "signos_detectados": [
    "Manchas negras o marrón oscuro en el haz de la hoja",
    "Bordes plumosos y difusos característicos de la lesión"
  ],
  "diagnosticos_diferenciales": [
    "Vello o Mildiu velloso (Peronospora sparsa)",
    "Daños mecánicos"
  ],
  "condiciones_compatibles_ecuador": [
    "Hojas mojadas por más de 6 horas continuas en invernaderos de Pichincha",
    "Salpicaduras de riego por aspersión"
  ],
  "nivel_severidad": "moderado",
  "accion_inmediata": [
    "Retirar de inmediato las hojas con síntomas visibles",
    "Mejorar la ventilación del invernadero"
  ],
  "manejo_integrado": {
    "cultural": [
      "Evitar la acumulación de humedad ambiental prolongada",
      "Saneamiento y recolección de hojarasca infectada"
    ],
    "quimico_biologico": [
      "Fungicidas específicos: Difenoconazol, Mancozeb o Clorotalonil",
      "Biocontrol con Bacillus subtilis"
    ]
  },
  "requiere_segunda_foto": false,
  "guia_captura_segunda_foto": {
    "organo_objetivo": "enves_hoja",
    "angulo_recomendado": "Foto macro perpendicular",
    "motivo": "Explicación agronómica"
  }
}
```

---

## 🔄 Cómo Manejar en la App la "Petición de Segunda Foto":

En tu interfaz móvil, evalúa la variable `requiere_segunda_foto`:
* **Si es `false`:** Muestra la pantalla de resultado con el diagnóstico, severidad y plan de tratamiento.
* **Si es `true`:** Muestra un modal interactivo al usuario diciendo:
  > *"Diagnóstico no concluyente. Por favor, {guia_captura_segunda_foto.angulo_recomendado}. Motivo: {guia_captura_segunda_foto.motivo}"*
  
  Y abre nuevamente la cámara enfocada en ese órgano para una segunda verificación.
