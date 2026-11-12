"""
Catálogo Fitopatológico de Rosas en Ecuador para el proyecto Mr. Rose.
Basado en investigación agronómica para Pichincha y Cotopaxi.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GuiaCaptura(BaseModel):
    organo_objetivo: str
    angulo_recomendado: str
    motivo: str


class EnfermedadInfo(BaseModel):
    id: str
    nombre_comun: str
    nombre_cientifico: str
    tipo_patogeno: str  # Hongo necrotrófico, biótrofo, oomicete, etc.
    organos_principales: List[str]
    signos_visuales_clave: List[str]
    diferenciador_clave: str
    condiciones_ecuador: List[str]
    diagnosticos_diferenciales: List[str]
    manejo_cultural: List[str]
    manejo_quimico_biologico: List[str]
    regla_segunda_foto: Optional[GuiaCaptura] = None


CATALOGO_ENFERMEDADES: Dict[str, EnfermedadInfo] = {
    "botrytis": EnfermedadInfo(
        id="botrytis",
        nombre_comun="Botrytis o Moho gris",
        nombre_cientifico="Botrytis cinerea",
        tipo_patogeno="Hongo necrotrófico",
        organos_principales=["Pétalos", "Botones florales", "Flores abiertas", "Hojas senescentes"],
        signos_visuales_clave=[
            "Manchas café claro o marrones en pétalos con bordes irregulares",
            "Pudrición blanda y acuosa de flores",
            "Moho o pelusa gris a gris pardusco sobre tejido en descomposición",
            "Botones florales que no abren o se oscurecen"
        ],
        diferenciador_clave="Moho gris perceptible sobre tejido en descomposición (especialmente pétalos/botones). No forma pústulas ni polvo blanco seco.",
        condiciones_ecuador=[
            "Humedad relativa alta persistente en zonas de Pichincha y Cotopaxi",
            "Condensación nocturna en invernaderos y mala circulación de aire",
            "Riego por aspersión que moja pétalos",
            "Heridas de manipulación o cosecha y presencia de pétalos senescentes"
        ],
        diagnosticos_diferenciales=["Oídio", "Vello", "Daño por frío o químicos", "Bacteriosis"],
        manejo_cultural=[
            "Retirar y destruir flores marchitas, pétalos caídos y restos vegetales (no compostar)",
            "Mejorar ventilación abriendo cortinas y aumentando distancia entre plantas",
            "Evitar mojar flores y follaje; regar al suelo o por goteo temprano en la mañana",
            "Manipular flores con cuidado para evitar heridas de cosecha"
        ],
        manejo_quimico_biologico=[
            "Aplicar fungicidas específicos registrados para Botrytis en rosa, rotando modos de acción (FRAC)",
            "Uso complementario de agentes biológicos (Bacillus subtilis, Trichoderma spp.)"
        ],
        regla_segunda_foto=GuiaCaptura(
            organo_objetivo="base_petalos_boton",
            angulo_recomendado="Macro en primer plano a la base de pétalos o cáliz del botón floral",
            motivo="Confirmar si existe esporulación de moho gris o si se trata de daño mecánico o quemadura solar"
        )
    ),
    "oidio": EnfermedadInfo(
        id="oidio",
        nombre_comun="Oídio o Mildeo polvoriento",
        nombre_cientifico="Podosphaera pannosa",
        tipo_patogeno="Hongo biótrofo",
        organos_principales=["Hojas jóvenes", "Brotes tiernos", "Tallos", "Botones"],
        signos_visuales_clave=[
            "Polvillo blanco o grisáceo harinoso superficial en haz, envés o tallos",
            "Deformación, enrollamiento y curvatura de hojas tiernas",
            "Aspecto ceniciento en botones con dificultad de apertura"
        ],
        diferenciador_clave="Polvillo blanco superficial que se desprende fácilmente. Afecta haz y envés sin requerir lámina de agua libre.",
        condiciones_ecuador=[
            "Días templados seguidos de noches frías con alta humedad relativa (típico clima interandino)",
            "Follaje denso y sombreado con aire estancado",
            "Exceso de fertilización nitrogenada que genera brotes excesivamente suculentos"
        ],
        diagnosticos_diferenciales=["Vello", "Roya", "Mancha negra", "Residuos de agroquímicos"],
        manejo_cultural=[
            "Eliminar brotes y hojas fuertemente infectados",
            "Poda sanitaria para desdensificar el dosel y mejorar penetración de luz",
            "Evitar riegos tardíos y regular fertilización de nitrógeno"
        ],
        manejo_quimico_biologico=[
            "Fungicidas protectores (azufre elemental en horas frescas) o sistémicos (triazoles/estrobilurinas)",
            "Biofungicidas y sales de potasio (bicarbonato de potasio)"
        ],
        regla_segunda_foto=GuiaCaptura(
            organo_objetivo="haz_y_brotes_jovenes",
            angulo_recomendado="Plano cenital con iluminación oblicua para resaltar la textura del micelio",
            motivo="Distinguir polvillo blanquecino de oídio frente a residuos de aspersión foliar o manchas cloróticas de vello"
        )
    ),
    "vello": EnfermedadInfo(
        id="vello",
        nombre_comun="Vello o Mildiu velloso",
        nombre_cientifico="Peronospora sparsa",
        tipo_patogeno="Pseudohongo oomicete",
        organos_principales=["Hojas", "Tallos", "Pedúnculos", "Cáliz"],
        signos_visuales_clave=[
            "Manchas angulosas delimitadas por nervaduras, de color púrpura, rojizo, café o negro en el haz",
            "Pelusilla o esporulación fina gris-violácea exclusivamente en el envés bajo alta humedad",
            "Amarillamiento sectorizado y defoliación rápida y severa",
            "Manchas purpúreas longitudinales en tallos y pedúnculos"
        ],
        diferenciador_clave="Manchas poliédricas limitadas por las venas de la hoja y esporulación gris presente ÚNICAMENTE en el envés.",
        condiciones_ecuador=[
            "Humedad relativa superior al 85% y película de agua líquida sobre hojas por más de 4 horas",
            "Temperaturas frescas (15°C a 20°C) muy frecuentes en las noches de la sierra ecuatoriana",
            "Riego al final de la tarde o goteo de condensación del plástico del invernadero"
        ],
        diagnosticos_diferenciales=["Oídio", "Mancha negra", "Roya", "Quemaduras por plaguicidas"],
        manejo_cultural=[
            "Eliminación urgente de follaje afectado del invernadero",
            "Manejo estricto de cortinas para evitar condensación y reducir humedad foliar nocturna",
            "Nunca regar al atardecer; regar a primeras horas de la mañana"
        ],
        manejo_quimico_biologico=[
            "Productos específicos para oomicetes (fosfonatos de potasio, metalaxil, dimetomorf, mancozeb preventivo)",
            "Alternar grupos químicos para prevenir resistencia rápida de Peronospora"
        ],
        regla_segunda_foto=GuiaCaptura(
            organo_objetivo="enves_hoja",
            angulo_recomendado="Primer plano macro del envés (cara inferior) de las hojas con manchas angulares",
            motivo="CRÍTICO: Verificar la presencia o ausencia de esporulación gris-violácea en el envés para diferenciar de Mancha Negra y Oídio"
        )
    ),
    "roya": EnfermedadInfo(
        id="roya",
        nombre_comun="Roya del rosal",
        nombre_cientifico="Phragmidium mucronatum",
        tipo_patogeno="Hongo basidiomiceto",
        organos_principales=["Envés foliar", "Pecíolos", "Tallos tiernos"],
        signos_visuales_clave=[
            "Pústulas pulverulentas prominentes de color naranja brillante, amarillo o negro en el envés",
            "Puntos cloróticos amarillentos en el haz que coinciden exactamente con la posición de las pústulas",
            "Defoliación que inicia desde las hojas basales hacia el tercio superior"
        ],
        diferenciador_clave="Presencia de pústulas elevadas (eruptivas) cargadas de esporas color óxido/naranja en el envés.",
        condiciones_ecuador=[
            "Humedad continua y temperaturas frescas a templadas",
            "Hojas mojadas por más de 6 horas continuas",
            "Permanencia de inóculo en hojas basales viejas sin saneamiento"
        ],
        diagnosticos_diferenciales=["Oídio", "Vello", "Mancha negra", "Picaduras de ácaros/insectos"],
        manejo_cultural=[
            "Retirar y quemar/enterrar hojas basales con pústulas; no dejar restos en el suelo",
            "Mejorar circulación de aire en los estratos inferiores de la planta",
            "Riego localizado al suelo evitando salpique"
        ],
        manejo_quimico_biologico=[
            "Fungicidas con acción específica antiroya (triazoles como tebuconazol/difenoconazol, oxicarboxina)",
            "Tratamientos preventivos con compuestos cúpricos o azufrados según época"
        ],
        regla_segunda_foto=GuiaCaptura(
            organo_objetivo="enves_hojas_basales",
            angulo_recomendado="Foto enfocada de la parte inferior de las hojas basales donde hay puntos amarillos",
            motivo="Confirmar si las manchas del haz corresponden a pústulas anaranjadas activas en el envés"
        )
    ),
    "mancha_negra": EnfermedadInfo(
        id="mancha_negra",
        nombre_comun="Mancha negra de la rosa",
        nombre_cientifico="Diplocarpon rosae",
        tipo_patogeno="Hongo ascomiceto",
        organos_principales=["Haz foliar (principalmente hojas inferiores y medias)", "Tallos"],
        signos_visuales_clave=[
            "Manchas negras o marrón muy oscuro, circulares o redondeadas, de 2 a 12 mm",
            "Bordes plumosos, estrellados o difusos muy característicos",
            "Halo clorótico (amarillo) alrededor de las manchas que termina en clorosis total y caída prematura de la hoja",
            "Afecta primero hojas maduras de la base y avanza en sentido ascendente"
        ],
        diferenciador_clave="Lesiones oscuras circulares planas con bordes plumosos rodeadas de un halo amarillo, sin micelio blanco ni pústulas.",
        condiciones_ecuador=[
            "Hojas mojadas por 6 o más horas continuas a temperaturas de 18°C a 24°C",
            "Salpicaduras de agua de lluvia o riego por aspersión que dispersan las conidias",
            "Falta de recolección de hojarasca infectada en el suelo del invernadero"
        ],
        diagnosticos_diferenciales=["Vello", "Oídio", "Roya", "Deficiencias nutricionales", "Manchas por fitotoxicidad"],
        manejo_cultural=[
            "Eliminar y destruir de inmediato hojas caídas y podar tallos con cancros oscuros",
            "Riego exclusivo por goteo; evitar completamente mojar el follaje",
            "Mantener el dosel abierto para secado rápido tras rocío o lluvia"
        ],
        manejo_quimico_biologico=[
            "Fungicidas protectores aplicados preventivamente (clorotalonil, mancozeb, captan)",
            "Fungicidas sistémicos curativos en primeras etapas (triazoles, estrobilurinas)"
        ],
        regla_segunda_foto=GuiaCaptura(
            organo_objetivo="haz_hoja_y_porte_general",
            angulo_recomendado="Foto perpendicular nítida a las manchas del haz y foto general de la posición en la planta",
            motivo="Verificar los márgenes plumosos de las manchas y evaluar la severidad de defoliación ascendente"
        )
    ),
    "sano": EnfermedadInfo(
        id="sano",
        nombre_comun="Tejido Sano / Sin Signos de Enfermedad",
        nombre_cientifico="Rosa sp. (Saludable)",
        tipo_patogeno="Ninguno",
        organos_principales=["Hojas", "Botones", "Flores", "Tallos"],
        signos_visuales_clave=[
            "Lámina foliar con color verde homogéneo, turgente y sin manchas necróticas",
            "Pétalos limpios sin decoloraciones, pudriciones ni moho",
            "Ausencia de pústulas, polvillo blanquecino o deformaciones"
        ],
        diferenciador_clave="Tejido vegetal con vigor, coloración uniforme y sin signos de ataque patógeno.",
        condiciones_ecuador=[
            "Manejo preventivo adecuado de humedad y ventilación",
            "Nutrición balanceada de macro y micronutrientes",
            "Programa fitosanitario preventivo eficaz"
        ],
        diagnosticos_diferenciales=["Enfermedad incipiente asintomática"],
        manejo_cultural=[
            "Mantener programas de monitoreo periódico semanal",
            "Continuar con riego localizado y podas de aireación"
        ],
        manejo_quimico_biologico=[
            "Aplicaciones preventivas periódicas según la temporada de lluvias o niebla"
        ]
    )
}

CLASES_CANONICAS = ["sano", "botrytis", "oidio", "vello", "roya", "mancha_negra"]
MAPA_ID_A_NOMBRE = {k: v.nombre_comun for k, v in CATALOGO_ENFERMEDADES.items()}
