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

        return f"""Eres el Asistente Fitopatólogo Experto 'Mr. Rose', especializado en el diagnóstico y manejo agronómico del cultivo de rosas en Ecuador (Pichincha y Cotopaxi).

BASE FITOPATOLÓGICA DE ECUADOR:
{catalogo_str}

REGLAS CRÍTICAS DE DIAGNÓSTICO:
1. El modelo local ya calculó un vector de probabilidades iniciales. Debes tomarlo en cuenta pero verificar visualmente la imagen.
2. Si la foto es ambigua, borrosa, o hay duda entre enfermedades parecidas:
   - VELLO vs OÍDIO: Si se ve mancha en el haz pero no se aprecia el envés, DEBES solicitar una segunda foto enfocando el envés para buscar esporulación gris-violácea.
   - BOTRYTIS: Si se sospecha moho gris en botón o pétalo pero no es concluyente, solicitar acercamiento macro a la base de pétalos o cáliz.
   - ROYA vs MANCHA NEGRA: Si hay dudas tempranas, pedir foto del envés de hojas basales.
3. Debes responder EXCLUSIVAMENTE con un objeto JSON válido con la siguiente estructura exacta:
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
        context_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía la imagen a Gemini con la base de conocimiento y el vector de probabilidades local.
        """
        if not self.is_available():
            # Fallback en caso de no tener API Key configurada
            return self._heuristic_fallback(classifier_probs)

        # Convertir imagen PIL a bytes JPEG
        buffered = io.BytesIO()
        image.convert("RGB").save(buffered, format="JPEG", quality=90)
        img_bytes = buffered.getvalue()

        prompt_usuario = (
            f"Analiza esta imagen de rosa cultivada en Ecuador.\n"
            f"El clasificador cuantitativo local arrojó las siguientes probabilidades:\n"
            f"{json.dumps(classifier_probs, indent=2)}\n"
        )
        if context_notes:
            prompt_usuario += f"\nNotas contextuales del agricultor: {context_notes}\n"

        prompt_usuario += "\nProporciona el diagnóstico agronómico estructurado en formato JSON estricto."

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                    prompt_usuario
                ],
                config=types.GenerateContentConfig(
                    system_instruction=self.build_system_prompt(),
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            result = json.loads(response.text)
            return result
        except Exception as e:
            print(f"[!] Error al llamar a Gemini: {e}. Activando motor heurístico de respaldo.")
            return self._heuristic_fallback(classifier_probs, error_note=str(e))

    def _heuristic_fallback(
        self,
        classifier_probs: Dict[str, float],
        error_note: Optional[str] = None
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
        requiere_segunda = top_conf < 0.80 or (top_conf - second_conf < 0.25 and top_class != "sano")
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
