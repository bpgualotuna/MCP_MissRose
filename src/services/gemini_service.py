"""
Servicio de Integración con Google AI Studio (Gemini Multimodal) para Mr. Rose MCP.
Combina la visión del modelo LLM con las probabilidades cuantitativas locales
y la base de conocimiento fitopatológico de Ecuador.
"""

import os
import json
import base64
import io
from typing import Dict, Any, Optional
from PIL import Image
from dotenv import load_dotenv

from src.knowledge.disease_catalog import CATALOGO_ENFERMEDADES

load_dotenv()


class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("[✓] GeminiService: Cliente de Google AI Studio inicializado correctamente.")
            except Exception as e:
                print(f"[!] GeminiService: Error al inicializar google-genai: {e}")
        else:
            print("[!] GeminiService: GEMINI_API_KEY no configurada. Funcionará en modo heurístico/local.")

    def is_available(self) -> bool:
        return self.client is not None

    def build_system_prompt(self) -> str:
        resumen_catalogo = []
        for eid, info in CATALOGO_ENFERMEDADES.items():
            resumen_catalogo.append(
                f"- ID: {eid} | Nombre: {info.nombre_comun} ({info.nombre_cientifico})\n"
                f"  Órganos: {', '.join(info.organos_principales)}\n"
                f"  Signos Clave: {'; '.join(info.signos_visuales_clave)}\n"
                f"  Diferenciador: {info.diferenciador_clave}\n"
                f"  Condiciones Ecuador: {'; '.join(info.condiciones_ecuador)}\n"
            )
        catalogo_str = "\n".join(resumen_catalogo)

        return f"""Eres la Dra. Miss Rose, Asistente Fitopatóloga Experta especializada en el diagnóstico y manejo agronómico del cultivo de rosas en Ecuador (Pichincha y Cotopaxi).

BASE FITOPATOLÓGICA DE ECUADOR:
{catalogo_str}

REGLAS CRÍTICAS DE DIAGNÓSTICO VISUAL (PRIORIDAD ABSOLUTA):
1. PRIMACÍA VISUAL: Tu propia inspección visual directa de la fotografía tiene PRIORIDAD ABSOLUTA sobre el vector de probabilidades del clasificador local ONNX.
2. SESGO CONOCIDO DEL MODELO LOCAL: El clasificador local ONNX fue entrenado mayoritariamente con hojas aisladas o fondos controlados/recortados; en fotos reales de celular con fondo natural de invernadero, suelo o manos, el modelo local suele equivocarse y sobrediagnosticar "botrytis" o confundir iluminación. Si tu observación visual contradice al modelo local, IGNORA el modelo local y confía en los signos reales que ves en la imagen.
3. CLAVES VISUALES PARA DESEMPATE EN FOTOS REALES:
   - BOTRYTIS: Ataca principalmente PÉTALOS Y BOTONES FLORALES (manchas café blandas/acuosas, moho o pelusa gris). NO diagnostiques botrytis en una hoja verde sana solo por el fondo.
   - OÍDIO: Polvillo blanco o grisáceo harinoso SUPERFICIAL sobre hojas jóvenes, brotes o botones (haz y envés), a veces con enrollamiento foliar.
   - VELLO (Mildiu velloso): Manchas ANGULOSAS púrpuras, rojizas o café delimitadas por las nervaduras en el haz; esporulación gris-violácea SOLO en el envés.
   - ROYA: Pústulas elevadas/polvorientas de color NARANJA, amarillo o negro en el ENVÉS (y puntos amarillos frente a ellas en el haz).
   - MANCHA NEGRA: Manchas circulares negras/marrón oscuro con BORDES PLUMOSOS/estrellados y halo amarillo alrededor en el haz.
   - SANO: Tejido verde uniforme o pétalos limpios sin lesiones patológicas (no confundir brillos de luz, gotas limpias o tierra con enfermedad).
4. AMBIGÜEDAD, FOTO LEJANA O DESENFOQUE:
   - Si la foto está muy lejana, borrosa, oscura o no permite distinguir los signos con certeza, asigna confianza < 0.70, usa "no_determinable" (o la hipótesis más probable) y activa "requiere_segunda_foto": true indicando acercamiento al órgano afectado.
   - Si hay mancha en el haz pero falta ver el envés para descartar Vello vs Oídio vs Roya, activa "requiere_segunda_foto": true pidiendo el envés foliar.
5. Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura exacta:
{{
  "diagnostico_probable": "nombre_canónico (sano, botrytis, oidio, vello, roya, mancha_negra, o no_determinable)",
  "nombre_comun": "Nombre legible de la enfermedad o estado sano",
  "nombre_cientifico": "Agente causal científico",
  "confianza": 0.85,  // Número entre 0.0 y 1.0
  "organos_afectados": ["hoja", "boton", "petalo", "tallo"],
  "signos_detectados": ["descripción clara del signo observado"],
  "diagnosticos_diferenciales": ["otras posibles causas a descartar"],
  "condiciones_compatibles_ecuador": ["humedad alta en invernadero", "condensacion nocturna", etc.],
  "nivel_severidad": "bajo / moderado / severo / no_aplica",
  "accion_inmediata": [
    "retirar hojas/flores infectadas",
    "mejorar ventilacion"
  ],
  "manejo_integrado": {{
    "cultural": ["recomendaciones de manejo de humedad, riego y poda"],
    "quimico_biologico": ["fungicidas específicos para la patología o productos biológicos"]
  }},
  "requiere_segunda_foto": false,  // true si la confianza < 0.80 o si falta ver el envés/botón
  "guia_captura_segunda_foto": {{
    "organo_objetivo": "enves_hoja / base_petalos / hojas_basales",
    "angulo_recomendado": "Instrucción precisa del ángulo e iluminación",
    "motivo": "Explicación agronómica de por qué se necesita esa foto"
  }}
}}"""

    def analyze_image(
        self,
        image: Image.Image,
        classifier_probs: Dict[str, float],
        context_notes: Optional[str] = None,
        second_image: Optional[Image.Image] = None
    ) -> Dict[str, Any]:
        """
        Envía la imagen (y una segunda toma opcional de envés/otro ángulo) a Gemini
        con la base de conocimiento y el vector de probabilidades local.
        """
        has_second_image = second_image is not None
        if not self.is_available():
            # Fallback en caso de no tener API Key configurada
            return self._heuristic_fallback(classifier_probs, has_second_image=has_second_image)

        # Convertir imagen principal PIL a bytes JPEG (limitando lado mayor a 1600px para preservar detalle sin saturar red)
        img_rgb = image.convert("RGB")
        if max(img_rgb.size) > 1600:
            img_rgb.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        buffered = io.BytesIO()
        img_rgb.save(buffered, format="JPEG", quality=92)
        img_bytes = buffered.getvalue()

        prompt_usuario = (
            f"Analiza visualmente esta fotografía real de rosa cultivada en Ecuador.\n"
            f"Referencia orientativa del clasificador ONNX local (recuerda: tiene sesgo en fondos reales y tiende a sobrediagnosticar botrytis; prioriza siempre tu observación visual directa):\n"
            f"{json.dumps(classifier_probs, indent=2)}\n"
        )
        if context_notes:
            prompt_usuario += f"\nNotas contextuales del agricultor: {context_notes}\n"

        last_error = None
        try:
            from google.genai import types
            request_contents = [
                types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
            ]
            if second_image is not None:
                sec_rgb = second_image.convert("RGB")
                if max(sec_rgb.size) > 1600:
                    sec_rgb.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                second_buffered = io.BytesIO()
                sec_rgb.save(second_buffered, format="JPEG", quality=92)
                second_img_bytes = second_buffered.getvalue()
                request_contents.append(
                    types.Part.from_bytes(data=second_img_bytes, mime_type="image/jpeg")
                )
                prompt_usuario += (
                    "\nSe adjunta una SEGUNDA IMAGEN correspondiente al segundo ángulo / envés foliar "
                    "solicitado para desempate diferencial. Evalúa ambas imágenes en conjunto y emite "
                    "un diagnóstico definitivo con \"requiere_segunda_foto\": false.\n"
                )

            prompt_usuario += "\nProporciona el diagnóstico agronómico estructurado en formato JSON estricto."
            request_contents.append(prompt_usuario)

            # Intentar primero con el modelo multimodal más preciso y hacer fallback si hay saturación (503)
            for model_name in ("gemini-3.8-flash", "gemini-3.5-flash-lite"):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=request_contents,
                        config=types.GenerateContentConfig(
                            system_instruction=self.build_system_prompt(),
                            response_mime_type="application/json",
                            temperature=0.1
                        )
                    )
                    raw_text = (response.text or "").strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.strip("`").removeprefix("json").strip()
                    result = json.loads(raw_text)
                    if has_second_image:
                        result["requiere_segunda_foto"] = False
                    return result
                except Exception as model_err:
                    last_error = model_err
                    print(f"[!] Falló modelo {model_name}: {model_err}")
                    continue

            raise last_error if last_error else RuntimeError("No se obtuvo respuesta de Gemini.")
        except Exception as e:
            print(f"[!] Error al llamar a Gemini: {e}. Activando motor heurístico de respaldo.")
            return self._heuristic_fallback(
                classifier_probs,
                error_note=str(e),
                has_second_image=has_second_image
            )

    def _heuristic_fallback(
        self,
        classifier_probs: Dict[str, float],
        error_note: Optional[str] = None,
        has_second_image: bool = False
    ) -> Dict[str, Any]:
        """
        Motor de respaldo cuando no hay conexión con Gemini.
        Aplica las reglas puras del catálogo de Ecuador sobre las probabilidades numéricas.
        """
        # Ordenar por probabilidad descendente
        sorted_probs = sorted(classifier_probs.items(), key=lambda x: x[1], reverse=True)
        top_class, top_conf = sorted_probs[0]
        second_class, second_conf = sorted_probs[1] if len(sorted_probs) > 1 else ("ninguno", 0.0)

        info = CATALOGO_ENFERMEDADES.get(top_class, CATALOGO_ENFERMEDADES["sano"])

        # Regla de segunda foto guiada: si confianza < 0.80 o si el segundo lugar está cerca
        requiere_segunda = (not has_second_image) and (
            top_conf < 0.80 or (top_conf - second_conf < 0.25 and top_class != "sano")
        )
        guia_captura = None

        if requiere_segunda and info.regla_segunda_foto:
            guia_captura = {
                "organo_objetivo": info.regla_segunda_foto.organo_objetivo,
                "angulo_recomendado": info.regla_segunda_foto.angulo_recomendado,
                "motivo": info.regla_segunda_foto.motivo
            }

        return {
            "diagnostico_probable": top_class,
            "nombre_comun": info.nombre_comun,
            "nombre_cientifico": info.nombre_cientifico,
            "confianza": float(round(top_conf, 3)),
            "organos_afectados": info.organos_principales,
            "signos_detectados": info.signos_visuales_clave[:2],
            "diagnosticos_diferenciales": [second_class] if second_class != "ninguno" else info.diagnosticos_diferenciales[:2],
            "condiciones_compatibles_ecuador": info.condiciones_ecuador,
            "nivel_severidad": "moderado" if top_class != "sano" else "no_aplica",
            "accion_inmediata": info.manejo_cultural[:2],
            "manejo_integrado": {
                "cultural": info.manejo_cultural,
                "quimico_biologico": info.manejo_quimico_biologico
            },
            "requiere_segunda_foto": requiere_segunda,
            "guia_captura_segunda_foto": guia_captura,
            "nota_sistema": "Diagnóstico generado por motor heurístico agronómico local (sin Gemini API)" if not error_note else f"Fallback por: {error_note}"
        }
