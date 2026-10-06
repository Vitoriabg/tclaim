import os
import re
import numpy as np
import spacy
from spacy.language import Language

SPACY_MODEL = os.getenv("SPACY_MODEL", "pt_core_news_lg")
nlp_seg = spacy.load(SPACY_MODEL, exclude=["parser"])
nlp_full = spacy.load(SPACY_MODEL)

# ===== Código copiado do notebook de pré-processamento =====

# Dicionário de abreviações jornalísticas e formais
_ABREVIACOES_TOKENS = {
    "prof", "profa", "dr", "dra", "sr", "sra", "srta", "exmo", "exma",
    "ilmo", "ilma", "v.sa", "v.exa", "pe", "pr", "bp", "ap", "eng",
    "arq", "adv", "bel", "cel", "ten", "cap", "maj", "gen", "alm",
    "sgt", "cb", "sold",
    "av", "r", "al", "trav", "rod", "est", "pca", "pça", "bl", "apto",
    "cj", "quad", "lote", "km",
    "s/a", "cia", "ltda", "eireli", "me", "epp", "s.a", "c.i.a",
    "jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set",
    "out", "nov", "dez", "seg", "ter", "qua", "qui", "sex", "sab",
    "sáb", "dom",
    "art", "arts", "par", "pág", "págs", "pag", "pags", "vol", "vols",
    "cap", "caps", "sec", "seç", "ed", "num", "núm", "n", "no", "nº",
    "tel", "cel", "fax", "ram", "cx", "dept", "depto",
    "obs", "etc", "ex", "exs", "fig", "figs", "ref", "refs", "coord",
    "org", "orgs", "trad", "apud", "ib", "ibid", "id", "op", "cit",
    "loc", "ca", "v", "vs", "min", "seg", "h",
    "a.c", "d.c", "a.m", "p.m", "i.e", "e.g", "cf", "fl", "fls"
}

def _eh_abreviacao(doc, idx_ponto):
    """Verifica se o ponto no índice idx_ponto faz parte de uma abreviação legítima."""
    if idx_ponto == 0:
        return False
    token_ant = doc[idx_ponto - 1]
    texto_ant = token_ant.text.lower().rstrip('.')

    if texto_ant in _ABREVIACOES_TOKENS:
        if texto_ant == "al":
            return (idx_ponto >= 2 and doc[idx_ponto - 2].text.lower() == "et")
        return True

    return False

_FIM_SENTENCA = {'.', '!', '?'}
_PARES_ABERTURA  = {'"': '"', '“': '”', '«': '»', '‘': '’', '(': ')', '[': ']', '{': '}'}
_PARES_FECHAMENTO = {v: k for k, v in _PARES_ABERTURA.items()}
_ASPAS_RETAS = {'"', "'"}

@Language.component("corrigir_fronteiras_estrito")
def corrigir_fronteiras_estrito(doc):
    nivel = 0
    aspas_retas_count = 0
    niveis = []
    for token in doc:
        for char in token.text:
            if char in _ASPAS_RETAS:
                aspas_retas_count += 1
                if aspas_retas_count % 2 == 1:
                    nivel += 1
                else:
                    nivel = max(0, nivel - 1)
            elif char in _PARES_ABERTURA:
                nivel += 1
            elif char in _PARES_FECHAMENTO:
                nivel = max(0, nivel - 1)
        niveis.append(nivel)

    for i, token in enumerate(doc):
        if i == 0:
            token.is_sent_start = True
        else:
            token.is_sent_start = False
            prev_token = doc[i - 1]
            nivel_prev = niveis[i - 1]
            encerra = False

            # Só permite quebra quando todos os delimitadores estiverem fechados (nível 0)
            if nivel_prev == 0:
                if prev_token.text in _FIM_SENTENCA:
                    if prev_token.text == '.':
                        if not _eh_abreviacao(doc, i - 1):
                            encerra = True
                    else:
                        encerra = True
                elif (i >= 2
                      and prev_token.text in (set(_PARES_FECHAMENTO) | _ASPAS_RETAS)
                      and doc[i - 2].text in _FIM_SENTENCA
                      and niveis[i - 2] == 0):
                    encerra = True

            if encerra:
                token.is_sent_start = True

    return doc

if "corrigir_fronteiras_estrito" not in nlp_seg.pipe_names:
    nlp_seg.add_pipe("corrigir_fronteiras_estrito", first=True)
print("Pipeline de segmentação estrita registrado!")


PRONOMES_SUJEITO = {
    "ele": ("Masc", "Sing"),
    "ela": ("Fem", "Sing"),
    "eles": ("Masc", "Plur"),
    "elas": ("Fem", "Plur")
}

DEMONSTRATIVOS_SUJEITO = {
    "este": ("Masc", "Sing"),
    "esta": ("Fem", "Sing"),
    "estes": ("Masc", "Plur"),
    "estas": ("Fem", "Plur"),
    "esse": ("Masc", "Sing"),
    "essa": ("Fem", "Sing"),
    "esses": ("Masc", "Plur"),
    "essas": ("Fem", "Plur"),
    "aquele": ("Masc", "Sing"),
    "aquela": ("Fem", "Sing"),
    "aqueles": ("Masc", "Plur"),
    "aquelas": ("Fem", "Plur")
}

VERBOS_INANIMADOS = {
    "quebrar", "rasgar", "fundir", "despejar", "vazar", "explodir",
    "danificar", "enferrujar", "amassar", "desconectar", "trincar",
    "estourar", "avariar", "romper", "desmoronar", "apagar",
    "chover", "ventar", "nevar", "gear", "relampear", "anoitecer"
}

VERBOS_ANIMADOS = {
    "dizer", "afirmar", "declarar", "explicar", "comentar", "perguntar",
    "responder", "gritar", "sussurrar", "pensar", "acreditar", "achar",
    "decidir", "prometer", "concordar", "discordar", "pedir", "exigir",
    "correr", "andar", "caminhar", "nadar", "pular", "saltar", "jogar",
    "comemorar", "lamentar", "chorar", "sorrir", "abraçar", "beijar",
    "morrer", "nascer", "adoecer", "sofrer", "sentir", "gostar", "amar",
    "odiar", "temer", "sonhar", "planejar", "querer", "desejar", "esperar",
    "estudar", "aprender", "ensinar", "treinar", "competir", "vencer", "perder"
}

SUBSTANTIVOS_HUMANOS = {
    "homem", "mulher", "menino", "menina", "garoto", "garota", "rapaz",
    "senhor", "senhora", "criança", "jovem", "adolescente", "adulto", "idoso",
    "presidente", "diretor", "ministro", "prefeito", "governador", "juiz",
    "médico", "doutor", "professor", "advogado", "engenheiro", "cientista",
    "atleta", "jogador", "treinador", "técnico", "piloto", "motorista",
    "policial", "soldado", "delegado", "agente", "pesquisador", "estudante",
    "pessoa", "indivíduo", "cidadão", "morador", "vizinho", "amigo", "colega",
    "pai", "mãe", "filho", "filha", "irmão", "irmã", "esposo", "esposa",
    "marido", "autor", "escritor", "jornalista", "repórter", "apresentador",
    "ator", "atriz", "cantor", "cantora", "músico", "artista",
    "goleiro", "zagueiro", "atacante", "lateral", "volante", "nadador", "nadadora"
}

SUBSTANTIVOS_ORGANIZACIONAIS = {
    "governo", "ministério", "tribunal", "senado", "câmara", "prefeitura",
    "empresa", "companhia", "corporação", "indústria", "fábrica", "loja",
    "banco", "instituição", "fundação", "associação", "sindicato", "partido",
    "universidade", "faculdade", "escola", "hospital", "clínica",
    "polícia", "exército", "marinha", "aeronáutica", "time", "clube"
}

def extrair_candidatos_avancado(doc_sent):
    candidatos = []
    for ent in doc_sent.ents:
        if ent.label_ in ("PER", "ORG", "LOC", "MISC"):
            genero = "Masc"
            numero = "Sing"
            for tok in ent:
                g = tok.morph.get("Gender")
                n = tok.morph.get("Number")
                if g: genero = g[0]
                if n: numero = n[0]
                break

            candidatos.append({
                "texto": ent.text,
                "lemma": ent.root.lemma_.lower(),
                "genero": genero,
                "numero": numero,
                "dep": ent.root.dep_,
                "root": ent.root,
                "is_person": (ent.label_ == "PER"),
                "is_org": (ent.label_ == "ORG"),
                "tipo_ent": ent.label_,
                "pos_idx": ent.root.i
            })

    for token in doc_sent:
        ja_coberto = any(token.idx >= ent.start_char and token.idx < ent.end_char for ent in doc_sent.ents)
        if ja_coberto:
            continue

        if token.pos_ in ("NOUN", "PROPN") and token.dep_ in ("nsubj", "nsubj:pass", "obj", "iobj", "appos"):
            genero = token.morph.get("Gender", [None])[0]
            numero = token.morph.get("Number", ["Sing"])[0]
            lemma = token.lemma_.lower()

            is_person = lemma in SUBSTANTIVOS_HUMANOS
            is_org = lemma in SUBSTANTIVOS_ORGANIZACIONAIS

            det_text = ""
            for child in token.children:
                if child.dep_ == "det" and child.i < token.i:
                    det_text = child.text
                    break

            if numero == "Plur":
                artigo_def = "Os" if genero == "Masc" else "As"
            else:
                artigo_def = "O" if genero == "Masc" else "A"

            if det_text.lower() in ("um", "uma", "uns", "umas"):
                texto_formatado = f"{artigo_def} {token.text}"
            elif det_text:
                texto_formatado = f"{det_text.capitalize()} {token.text}"
            else:
                texto_formatado = f"{artigo_def} {token.text}" if token.pos_ == "NOUN" else token.text

            candidatos.append({
                "texto": texto_formatado,
                "lemma": lemma,
                "genero": genero,
                "numero": numero,
                "dep": token.dep_,
                "root": token,
                "is_person": is_person,
                "is_org": is_org,
                "tipo_ent": None,
                "pos_idx": token.i
            })

    return candidatos

def pontuar_candidato(cand, pronome_tok, verbo_tok, dist_sentenca=1):
    verbo_lemma = verbo_tok.lemma_.lower()
    score = 0.0

    if cand["dep"] in ("nsubj", "nsubj:pass"):
        score += 3.2
    elif cand["dep"] == "obj":
        score += 1.8
    elif cand["dep"] == "appos":
        score += 1.5
    else:
        score += 0.3

    score -= (dist_sentenca - 1) * 2.0

    eh_animado = cand["is_person"] or cand["is_org"]

    if verbo_lemma in VERBOS_INANIMADOS:
        if cand["is_person"]:
            score -= 10.0
        elif cand["is_org"]:
            score -= 2.0
        else:
            score += 3.0

    if verbo_lemma in VERBOS_ANIMADOS:
        if cand["is_person"]:
            score += 3.5
        elif cand["is_org"]:
            score += 1.5
        else:
            score -= 4.0

    if cand["root"].has_vector and verbo_tok.has_vector:
        sim = cand["root"].similarity(verbo_tok)
        if not np.isnan(sim):
            score += sim * 2.5

    return score

def resolver_correferencias_avancado(sentencas, nlp, janela=3, score_minimo=1.0, margem_seguranca=0.5, verbose=False):
    sentencas_corrigidas = []
    logs_substituicoes = []
    historico_candidatos = []

    for i, sent_text in enumerate(sentencas):
        doc = nlp(sent_text)
        candidatos_atuais = extrair_candidatos_avancado(doc)

        if i == 0:
            sentencas_corrigidas.append(sent_text)
            logs_substituicoes.append("")
            historico_candidatos.append(candidatos_atuais)
            continue

        hist = list(reversed(historico_candidatos[-janela:]))
        substituicoes = []
        log_desta_sentenca = []

        for token in doc:
            pronome_lower = token.text.lower()
            tipo_pron = None
            genero_pron, numero_pron = None, None

            if token.pos_ == "PRON" and pronome_lower in PRONOMES_SUJEITO and token.dep_ in ("nsubj", "nsubj:pass"):
                genero_pron, numero_pron = PRONOMES_SUJEITO[pronome_lower]
                tipo_pron = "pessoal"
            elif token.pos_ in ("DET", "PRON") and pronome_lower in DEMONSTRATIVOS_SUJEITO and token.dep_ in ("nsubj", "nsubj:pass"):
                genero_pron, numero_pron = DEMONSTRATIVOS_SUJEITO[pronome_lower]
                tipo_pron = "demonstrativo"

            if tipo_pron:
                verbo = token.head
                candidatos_pontuados = []
                for dist, cands_sent in enumerate(hist, start=1):
                    for cand in cands_sent:
                        if cand["numero"] != numero_pron:
                            continue
                        if cand["genero"] and genero_pron and cand["genero"] != genero_pron:
                            continue
                        if cand["texto"].lower() == pronome_lower:
                            continue

                        sc = pontuar_candidato(cand, token, verbo, dist_sentenca=dist)
                        candidatos_pontuados.append((sc, cand))

                candidatos_pontuados.sort(key=lambda x: x[0], reverse=True)

                if candidatos_pontuados:
                    melhor_score, melhor_cand = candidatos_pontuados[0]

                    eh_seguro = True
                    if melhor_score < score_minimo:
                        eh_seguro = False
                        if verbose:
                            print(f"  [PISO MÍNIMO] Sentença {i+1}: '{token.text}' mantido (score {melhor_score:.2f} < {score_minimo})")
                    elif len(candidatos_pontuados) > 1:
                        segundo_score, segundo_cand = candidatos_pontuados[1]
                        diferenca = melhor_score - segundo_score
                        if diferenca < margem_seguranca:
                            eh_seguro = False
                            if verbose:
                                print(f"  [AMBIGUIDADE] Sentença {i+1}: '{token.text}' mantido (diferença {diferenca:.2f} < {margem_seguranca})")

                    if eh_seguro:
                        antecedente = melhor_cand["texto"]
                        if token.text[0].isupper():
                            antecedente_final = antecedente[0].upper() + antecedente[1:]
                        else:
                            if melhor_cand.get("is_person") or melhor_cand.get("tipo_ent") in ("PER", "ORG"):
                                antecedente_final = antecedente
                            else:
                                antecedente_final = antecedente[0].lower() + antecedente[1:]

                        substituicoes.append((token.idx, token.idx + len(token.text), antecedente_final))
                        log_desta_sentenca.append(f"{token.text} -> {antecedente_final}")
                        if verbose:
                            print(f"  [SUBSTITUIÇÃO OK] Sentença {i+1}: '{token.text}' -> '{antecedente_final}' (Score: {melhor_score:.2f})")

        texto_corrigido = sent_text
        for inicio, fim, novo in sorted(substituicoes, key=lambda x: x[0], reverse=True):
            texto_corrigido = texto_corrigido[:inicio] + novo + texto_corrigido[fim:]

        sentencas_corrigidas.append(texto_corrigido)
        logs_substituicoes.append(" | ".join(log_desta_sentenca))
        historico_candidatos.append(candidatos_atuais)

    return sentencas_corrigidas, logs_substituicoes

print("Funções de correferência contextual carregadas com sucesso!")

def extrair_features(texto):
    doc = nlp_full(str(texto))

    palavras = [token for token in doc if not token.is_punct and not token.is_space]
    qtd_palavras = len(palavras)

    if qtd_palavras == 0:
        return 0.0, 0, 0.0, 0, 0

    densidade_entidades = len(doc.ents) / qtd_palavras
    qtd_verbos = sum(1 for token in doc if token.pos_ in ['VERB', 'AUX'])
    densidade_verbos = qtd_verbos / qtd_palavras
    tem_numero = 1 if any(char.isdigit() for char in str(texto)) else 0
    eh_pergunta = 1 if str(texto).strip().endswith('?') else 0

    return densidade_entidades, qtd_palavras, densidade_verbos, tem_numero, eh_pergunta




# ===== Orquestração (equivale à "EXECUÇÃO PRINCIPAL" do notebook) =====
def analisar_texto(texto: str) -> list[dict]:
    doc_seg = nlp_seg(str(texto))
    sentencas_orig = [s.text.strip() for s in doc_seg.sents if s.text.strip()]
    if not sentencas_orig:
        return []
    sentencas_corr, _ = resolver_correferencias_avancado(
        sentencas_orig, nlp_full, janela=3, score_minimo=1.0,
        margem_seguranca=0.5, verbose=False)
    saida = []
    for s_orig, s_corr in zip(sentencas_orig, sentencas_corr):
        de, qp, dv, tn, ep = extrair_features(s_corr)
        saida.append({
            "sentenca_original": s_orig,
            "sentenca": s_corr,
            "densidade_entidades": de,
            "qtd_palavras": qp,
            "densidade_verbos": dv,
            "tem_numero": tn,
            "eh_pergunta": ep,
        })
    return saida
