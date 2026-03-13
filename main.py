import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import os
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.common import I2of5 
import textwrap


#--Desenvolvido por BRUNO DOMINGOS DE LIMA - Desenvolvedor - contato: (11) 992290567 - email: domingose837@gmail.com

# --- CONFIGURAÇÕES GERAIS ---
LARGURA_PAGINA = 210 * mm
ALTURA_PAGINA = 99 * mm
Y_FIXO = 0  

def format_inscricao(val):
    if pd.isna(val) or str(val).strip() == "": return "00000000"
    limpo = str(val).strip().replace('.', '').replace('-', '')
    return limpo.zfill(8)

def format_quadra_lote(val):
    if pd.isna(val) or str(val).strip() == "": return "0000"
    limpo = str(val).strip().replace('.0', '')
    return limpo.zfill(4)

def format_money(val):
    if pd.isna(val) or val == 0 or val == "0" or str(val).strip() == "": return "0,00"
    val_str = str(val).strip()
    try:
        if '.' in val_str and ',' not in val_str:
            v = float(val_str)
        elif ',' in val_str:
            v = float(val_str.replace('.', '').replace(',', '.'))
        else:
            val_limpo = val_str.lstrip('0')
            if not val_limpo: return "0,00"
            v = float(val_limpo) / 100
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

def format_date(dt):
    if pd.isna(dt) or str(dt).strip() == "": return ""
    s = str(dt).strip().replace('.0', '')
    if len(s) == 8 and s.isdigit():
        return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"
    return s

def clean_full(val):
    if pd.isna(val) or str(val).strip() == "": return ""
    texto = str(val).strip()
    try:
        texto = texto.encode('latin-1').decode('utf-8')
    except: pass
    reparos = {
        'Ãn': 'Ô', 'Ã\xad': 'Í', 'Ã³': 'Ó', 'Ã§': 'Ç', 
        'Ã£': 'Ã', 'Ãª': 'Ê', 'Ã©': 'É', 'Ã¡': 'Á',
        'Ã\x9a': 'Ú', 'Ãš': 'Ú'
    }
    for errado, correto in reparos.items():
        texto = texto.replace(errado, correto)
    
    # Remove espaços duplos para evitar palavras coladas no PDF
    texto = " ".join(texto.split())
    return texto.upper()

# --- INTELIGÊNCIA: NOME E RESPONSABILIDADE (CPF/CNPJ) ---
def get_nome_completo(d):
    prop = clean_full(d.get('Proprietario', ''))
    col_comp = next((k for k in d.keys() if 'compromiss' in k.lower() and 'cnpj' not in k.lower() and 'cpf' not in k.lower()), None)
    comp = clean_full(d.get(col_comp, '')) if col_comp else ''
    
    if prop and comp:
        return f"COMPROMISSÁRIO: {comp} / PROPRIETÁRIO: {prop}"
    elif comp:
        return f"COMPROMISSÁRIO: {comp}"
    elif prop:
        return f"PROPRIETÁRIO: {prop}"
    return ""

def get_documento(d):
    col_comp = next((k for k in d.keys() if 'compromiss' in k.lower() and 'cnpj' not in k.lower() and 'cpf' not in k.lower()), None)
    comp = clean_full(d.get(col_comp, '')) if col_comp else ''
    
    if comp:
        col_doc_comp = next((k for k in d.keys() if ('cpf' in k.lower() or 'cnpj' in k.lower()) and 'compromiss' in k.lower()), None)
        if col_doc_comp:
            doc = clean_full(d.get(col_doc_comp, ''))
            if doc: return doc
            
    col_doc_prop = next((k for k in d.keys() if ('cpf' in k.lower() or 'cnpj' in k.lower()) and 'prop' in k.lower()), None)
    if col_doc_prop:
        doc = clean_full(d.get(col_doc_prop, ''))
        if doc: return doc
        
    col_doc = next((k for k in d.keys() if 'cpf' in k.lower() or 'cnpj' in k.lower()), 'Cnpj/Cpf do Contribuinte')
    return clean_full(d.get(col_doc, ''))

# --- Funções de preenchimento de dados ---
def preencher_recibo(c, d, y):
    def clean(key): return clean_full(d.get(key))

    nome_completo = get_nome_completo(d)
    linhas_nome = textwrap.wrap(nome_completo, width=70) 
    
    c.setFont("Helvetica-Bold", 8 if len(linhas_nome) > 1 else 9)
    for i, ln in enumerate(linhas_nome[:3]): 
        c.drawString(15*mm, (y + 63.5*mm) - (i * 3.5*mm), ln)
    
    ajuste_y_nome = 3.5 * mm if len(linhas_nome) == 3 else 0

    c.setFont("Helvetica-Bold", 8)
    rua = clean('EndereÃ§o de Entrega com a descriÃ§Ã£o do Tipo de Logradouro')
    if not rua: rua = clean('EndereÃ§o de Entrega')
    num = clean('NÃºmero de Entrega') or clean('Numero Entrega')
    compl = clean('Complemento de Entrega')
    
    endereco_completo = f"{rua}, {num}"
    if compl:
        endereco_completo += f" - {compl}"
        
    linhas_endereco = textwrap.wrap(endereco_completo, width=82)
    ajuste_y = ajuste_y_nome 
    
    if len(linhas_endereco) > 0:
        c.drawString(15*mm, (y + 56*mm) - ajuste_y_nome, f"Endereço: {linhas_endereco[0]}")
        if len(linhas_endereco) > 1:
            resto = " ".join(linhas_endereco[1:])
            c.drawString(30*mm, (y + 53.5*mm) - ajuste_y_nome, resto)
            ajuste_y += 3.5 * mm 
    else:
        c.drawString(15*mm, (y + 56*mm) - ajuste_y_nome, "Endereço: ")
    
    y_bairro = (y + 51*mm) - ajuste_y + 0.5*mm
    y_cidade = (y + 46*mm) - ajuste_y + 0.5*mm
    y_estado = (y + 41*mm) - ajuste_y + 0.5*mm
    y_cep    = (y + 36*mm) - ajuste_y + 0.5*mm
    y_insc   = (y + 31*mm) - ajuste_y + 0.5*mm

    c.drawString(15*mm, y_bairro, f"Bairro: {clean('Bairro de Entrega') or clean('Bairro Entrega')}")
    c.drawString(15*mm, y_cidade, f"Cidade: {clean('Cidade de Entrega') or 'CESÁRIO LANGE'}")
    c.drawString(15*mm, y_estado, f"Estado: {clean('UF de Entrega') or 'SP'}")
    c.drawString(15*mm, y_cep, f"CEP: {clean('Cep de Entrega') or clean('CEP Entrega')}")
    
    insc_8 = format_inscricao(d.get('InscriÃ§Ã£o Cadastral'))
    c.drawString(15*mm, y_insc, f"Inscrição Imobiliária: {insc_8}")

def preencher_capa(c, d, y):    
    c.setFont("Helvetica-Bold", 12)

def preencher_demonstrativo(c, d, y, col_u_venc=None, col_u_liq=None):
    def clean(key): return clean_full(d.get(key))

    AJUSTE_GERAL_Y = 27    
    ESPACO_LINHAS = 7.0    
    ESPACO_VALOR = 4       
    
    c1, c2, c3, c4 = 16*mm, 51*mm, 86*mm, 121*mm

    f_label, s_label = "Helvetica-Bold", 5.7
    f_val, s_val = "Helvetica-Bold", 6.5

    y_r1 = y + (AJUSTE_GERAL_Y * mm)
    y_r2 = y_r1 - (ESPACO_LINHAS * mm)
    y_r3 = y_r2 - (ESPACO_LINHAS * mm)
    v_off = ESPACO_VALOR * mm

    y_end = y + 46*mm 
    
    nome_completo = get_nome_completo(d)
    linhas_nome = textwrap.wrap(nome_completo, width=70)
    c.setFont(f_val, 6.5 if len(linhas_nome) > 1 else 7.5)
    for i, ln in enumerate(linhas_nome[:3]):
        c.drawString(c1, (y_end + 9.5*mm) - (i * 3*mm), ln)
    
    c.setFont(f_label, s_label)
    c.drawString(c1, y_end, "ENDEREÇO DO IMÓVEL")
    c.drawString(c3, y_end, "ENDEREÇO PARA ENTREGA")
    
    c.setFont(f_val, s_val)
    end_lin1 = f"{clean('Logradouro do ImÃ³vel')} {clean('NÃºmero do ImÃ³vel')} {clean('Complemento do ImÃ³vel')}"
    c.drawString(c1, y_end - v_off, end_lin1[:50])
    
    c.drawString(c1, y_end - v_off - 3*mm, clean('Bairro do ImÃ³vel'))
    
    cid_cep = f"{clean('Cep do ImÃ³vel')} {clean('Cidade do ImÃ³vel')} - {clean('UF do ImÃ³vel')}"
    c.drawString(c1, y_end - v_off - 6*mm, cid_cep)

    c.setFont(f_label, s_label)
    quadra_4 = format_quadra_lote(d.get('Quadra do Loteamento'))
    lote_4 = format_quadra_lote(d.get('Lote'))
    c.drawString(c1, y_end - v_off - 10*mm, f"QUADRA: {quadra_4}")
    c.drawString(c1 + 40*mm, y_end - v_off - 10*mm, f"LOTE: {lote_4}")

    c.setFont(f_val, s_val)
    
    rua_ent = clean('EndereÃ§o de Entrega com a descriÃ§Ã£o do Tipo de Logradouro')
    if not rua_ent: rua_ent = clean('EndereÃ§o de Entrega')
    num_ent = clean('NÃºmero de Entrega') or clean('Numero Entrega')
    compl_ent = clean('Complemento de Entrega')
    
    end_ent_lin1 = f"{rua_ent.strip()}, {num_ent.strip()}"
    if compl_ent.strip():
        end_ent_lin1 += f" - {compl_ent.strip()}"
        
    ajuste_y_dem = 0 
    linhas_endereco_dem = []
    
    if "COMPL" in end_ent_lin1:
        partes = end_ent_lin1.split("COMPL")
        linha1 = partes[0].strip()
        if linha1.endswith("-") or linha1.endswith(":") or linha1.endswith(","):
            linha1 = linha1[:-1].strip()
        linhas_endereco_dem.append(linha1)
        linha2_completa = "COMPL" + partes[1]
        linhas_endereco_dem.extend(textwrap.wrap(linha2_completa, width=42))
    else:
        linhas_endereco_dem = textwrap.wrap(end_ent_lin1, width=42)
        
    for i, linha in enumerate(linhas_endereco_dem):
        c.drawString(c3, y_end - v_off - (i * 3*mm), linha)
        
    if len(linhas_endereco_dem) > 1:
        ajuste_y_dem = (len(linhas_endereco_dem) - 1) * 3 * mm
    
    bairro_ent = clean('Bairro de Entrega') or clean('Bairro Entrega')
    c.drawString(c3, y_end - v_off - 3*mm - ajuste_y_dem + 0.5*mm, bairro_ent[:45])
    
    cep_ent = clean('Cep de Entrega') or clean('CEP Entrega')
    cid_ent = clean('Cidade de Entrega') or clean('Cidade Entrega')
    uf_ent = clean('UF de Entrega') or clean('UF Entrega')
    
    cid_cep_ent = f"{cep_ent} {cid_ent} - {uf_ent}".strip()
    if cid_cep_ent == "-": cid_cep_ent = "" 
    
    c.drawString(c3, y_end - v_off - 6*mm - ajuste_y_dem + 0.5*mm, cid_cep_ent[:45])

    ult_venc = ""
    for i in range(12, 0, -1):
        v_p = d.get(f'Valor Total da Parcela {i}')
        dt_p = d.get(f'Data de Vencimento da Parcela {i}')
        if pd.notna(v_p) and pd.notna(dt_p) and str(dt_p).strip() != "":
            try:
                if float(str(v_p).replace(',', '.')) > 0:
                    ult_venc = dt_p
                    break
            except: pass
    
    if not ult_venc: 
        for i in range(12, 0, -1):
            dt_p = d.get(f'Data de Vencimento da Parcela {i}')
            if pd.notna(dt_p) and str(dt_p).strip() != "":
                ult_venc = dt_p
                break

    c.setFont(f_label, s_label)
    c.drawString(c1, y_r1, "ÁREA TERRENO")
    c.drawString(c2, y_r1, "V. VENAL TERRIT.")
    c.drawString(c3, y_r1, "1º VENCIMENTO")
    c.drawString(c4, y_r1, "TOTAL IPTU")
    
    c.setFont(f_val, s_val)
    c.drawString(c1, y_r1 - v_off, clean('Ãrea do Terreno'))
    c.drawString(c2, y_r1 - v_off, format_money(d.get('Valor Venal do Terreno', 0)))
    c.drawString(c3, y_r1 - v_off, format_date(d.get('Data de Vencimento da Parcela 1')))
    c.drawString(c4, y_r1 - v_off, format_money(d.get('Valor Total', 0)))

    c.setFont(f_label, s_label)
    c.drawString(c1, y_r2, "AREA CONSTR.")
    c.drawString(c2, y_r2, "V. VENAL PREDIAL")
    c.drawString(c3, y_r2, "ULT. VENCIMENTO")
    c.drawString(c4, y_r2, "VALOR C. ÚNICA")
    
    c.setFont(f_val, s_val)
    c.drawString(c1, y_r2 - v_off - 2, clean('Ãrea ConstruÃ­da Total'))
    c.drawString(c2, y_r2 - v_off - 2, format_money(d.get('Valor Venal Total da ConstruÃ§Ã£o', 0)))
    c.drawString(c3, y_r2 - v_off - 2, format_date(ult_venc))
    
    v_unica_liq = d.get(col_u_liq, 0) if col_u_liq else 0
    c.drawString(c4, y_r2 - v_off - 2, format_money(v_unica_liq))

    c.setFont(f_label, s_label)
    c.drawString(c1, y_r3 - 3, "TESTADA")
    c.drawString(c2, y_r3 - 3, "V. VENAL TOTAL")
    c.drawString(c3, y_r3 - 3, "VENC. C. ÚNICA")
    c.drawString(c4, y_r3 - 3, "VALOR PARCELA")
     
    c.setFont(f_val, s_val)
    c.drawString(c1, y_r3 - v_off - 6, clean('Testada Principal '))
    c.drawString(c2, y_r3 - v_off - 6, format_money(d.get('Valor Venal do ImÃ³vel', 0)))
    
    v_unica_venc = d.get(col_u_venc) if col_u_venc else ""
    c.drawString(c3, y_r3 - v_off - 6, format_date(v_unica_venc))
    
    c.drawString(c4, y_r3 - v_off - 6, format_money(d.get('Valor Total da Parcela 1', 0)))
 
    x_canhoto = c4 + 100
    x_valor = x_canhoto + 40*mm 
    
    insc_8 = format_inscricao(d.get('InscriÃ§Ã£o Cadastral'))

    y_canhoto = y_end + 43*mm
    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'INSCRIÇÃO IMOBILIÁRIA')
    c.setFont(f_val, s_val)
    c.drawString(x_canhoto, y_canhoto - v_off, insc_8)

    y_canhoto = y_end + 34*mm
    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'CPF/CNPJ')
    c.setFont(f_val, s_val)
    doc_responsavel = get_documento(d)
    c.drawString(x_canhoto, y_canhoto - v_off, doc_responsavel)

    y_canhoto = y_end + 25*mm
    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'EXERCÍCIO')
    c.drawString(x_canhoto, y_canhoto - v_off, clean('ExercÃ­cio do LanÃ§amento') or "2026")

    y_canhoto = y_end + 16*mm
    x_valor -= 10*mm

    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'IMPOSTO PREDIAL:')
    c.setFont(f_val, s_val)
    c.drawString(x_valor, y_canhoto, format_money(d.get('Valor do Tributo 1', 0)))

    y_canhoto = y_end + 12*mm
    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'IMPOSTO TERRITORIAL:')
    c.setFont(f_val, s_val)
    c.drawString(x_valor, y_canhoto, format_money(d.get('Valor do Tributo 2', 0)))

    y_canhoto = y_end + 8*mm
    c.setFont(f_label, s_label)
    c.drawString(x_canhoto, y_canhoto, 'TAXA COLETA LIXO:')
    c.setFont(f_val, s_val)
    c.drawString(x_valor, y_canhoto, format_money(d.get('Valor do Tributo 3', 0)))

    c.setFont(f_label, 7)
    c.drawString(c4 + 100, y_r3 - v_off - 6, f"TOTAL: R$ {format_money(d.get('Valor Total', 0))}")

    x_barcode = 8*mm  
    y_barcode = y + 30*mm 
    barcode_value = insc_8

    c.saveState()
    c.translate(x_barcode, y_barcode)
    c.rotate(90)
    
    barcode = code128.Code128(barcode_value, barHeight=5*mm, barWidth=0.3*mm)
    barcode.drawOn(c, 0, 0)
    
    c.setFont("Helvetica-Bold", 6)
    c.drawString(30, -3*mm, barcode_value) 
    c.restoreState()

def preencher_boleto(c, d, y, p_idx, total_p):
    def clean(key): return clean_full(d.get(key))

    insc_8 = format_inscricao(d.get('InscriÃ§Ã£o Cadastral'))

    is_unica = "nica" in str(p_idx).lower()
    
    if is_unica:
        col_venc = p_idx.replace('Valor Total da', 'Data de Vencimento da')
        col_venc = col_venc if col_venc in d else f'Data de Vencimento da Parcela {p_idx.split()[-1]}'
        val_col = p_idx 
        
        col_linha = p_idx.replace('Valor Total da', 'Linha DigitÃ¡vel da Parcela')
        if col_linha not in d:
             col_linha = next((k for k in d.keys() if "Linha" in k and "nica 1" in k), 'Linha DigitÃ¡vel da Parcela Ãšnica 1')
        linha = d.get(col_linha, '')
        
        txt_p_pdf = "ÚNICA"
    else:
        suffix = p_idx
        col_venc = f'Data de Vencimento da Parcela {suffix}'
        val_col = f'Valor Total da Parcela {suffix}'
        linha = d.get(f'Linha DigitÃ¡vel da Parcela {p_idx}', '')
        txt_p_pdf = f"{suffix}/{total_p}"

    venc = format_date(d.get(col_venc))
    valor = format_money(d.get(val_col, 0))
    exercicio = "2026"

    if pd.notna(linha) and str(linha).strip() != "":
        cod_baixa = str(linha).split()[-1]
    else:
        cod_baixa = f"{insc_8}-00{clean('Cadastro')}"

    c.setFont("Helvetica-Bold", 7)
    y_canhoto = y + 68*mm
    
    c.drawString(25*mm, y_canhoto, insc_8)
    c.drawString(95*mm, y_canhoto, insc_8)
    c.drawString(130*mm, y_canhoto, exercicio)
    c.drawString(150*mm, y_canhoto, cod_baixa)
    c.drawString(190*mm, y_canhoto, txt_p_pdf)
    c.drawString(60*mm, y_canhoto, txt_p_pdf)
    
    y_linha2 = y + 53*mm
    
    nome = get_nome_completo(d)
    doc_responsavel = get_documento(d)
    
    if doc_responsavel:
        texto_completo = f"{nome} - {doc_responsavel}"
    else:
        texto_completo = nome 
    
    linhas_nome_doc = textwrap.wrap(texto_completo, width=53) 
    
    if len(linhas_nome_doc) >= 3:
        c.setFont("Helvetica-Bold", 5.5)
        for i, linha_txt in enumerate(linhas_nome_doc[:3]):
            y_pos = (y_linha2 + 6*mm) - (i * 3*mm)
            c.drawString(16*mm, y_pos, linha_txt) 
            c.drawString(85*mm, y_pos, linha_txt) 
    elif len(linhas_nome_doc) == 2:
        c.setFont("Helvetica-Bold", 5.5)
        c.drawString(16*mm, y_linha2 + 3.5*mm, linhas_nome_doc[0]) 
        c.drawString(16*mm, y_linha2, linhas_nome_doc[1])                
        c.drawString(85*mm, y_linha2 + 3.5*mm, linhas_nome_doc[0])
        c.drawString(85*mm, y_linha2, linhas_nome_doc[1])
    else:
        c.setFont("Helvetica-Bold", 5.5)
        c.drawString(16*mm, y_linha2 + 1.5*mm, linhas_nome_doc[0])
        c.drawString(85*mm, y_linha2 + 1.5*mm, linhas_nome_doc[0])

    y_canhoto = y_linha2 - 8*mm
    c.setFont("Helvetica-Bold", 7)
    c.drawString(25*mm, y_canhoto, cod_baixa)
    c.drawString(58*mm, y_canhoto, exercicio)
    c.drawString(105*mm, y_canhoto, venc)
    c.drawString(165*mm, y_canhoto, valor)

    y_canhoto -= 8*mm
    c.drawString(55*mm, y_canhoto, venc)
    c.drawString(25*mm, y_canhoto, valor)

    if pd.notna(linha) and str(linha).strip() != "":
        y_canhoto -= 15*mm
        c.setFont("Courier", 8)
        c.drawString(95*mm, y_canhoto, str(linha))
        
        d_linha = "".join(filter(str.isdigit, str(linha)))
        
        bc_clean = ""
        if len(d_linha) == 47:
            bc_clean = d_linha[0:4] + d_linha[32:47] + d_linha[4:9] + d_linha[10:20] + d_linha[21:31]
        elif len(d_linha) == 48:
            bc_clean = d_linha[0:11] + d_linha[12:23] + d_linha[24:35] + d_linha[36:47]

        if len(bc_clean) == 44:
            barcode = I2of5(bc_clean, barHeight=10*mm, barWidth=0.28*mm, ratio=2.2, bearers=0, checksum=0, quiet=True, lquiet=4*mm, rquiet=4*mm)
            barcode.drawOn(c, 94*mm, y + 6.5*mm)

# --- EXECUÇÃO ---

try:
    print("Carregando CSV de IPTU...")
    df = pd.read_csv('resultado_IPTU.csv', sep=';', encoding='latin-1', dtype=str, low_memory=False)
    
    col_u_total = next((c for c in df.columns if "Valor Total" in c and "nica 1" in c), None)
    col_u_venc = next((c for c in df.columns if "Vencimento" in c and "nica 1" in c), None)
    col_u_liq = next((c for c in df.columns if "Valor L" in c and "nica 1" in c), None)

    def check_val_prio(val):
        if pd.isna(val): return 0
        v_limpo = str(val).strip().replace(',', '.')
        try:
            return 1 if float(v_limpo) > 0 else 0
        except:
            return 0

    if col_u_total:
        print("Ordenando por Parcela Única...")
        df['_sort_u'] = df[col_u_total].apply(check_val_prio)
        df = df.sort_values(by='_sort_u', ascending=False).drop(columns=['_sort_u'])

    print(f"Lidos {len(df)} registros. Iniciando processamento em lotes de até 21.000 páginas...")

    # Variáveis de controle de lotes
    MAX_PAGINAS_POR_ARQUIVO = 10500
    arquivo_idx = 1
    paginas_atuais = 0
    
    nome_arquivo = f"PRODUCAO_CARNES_IPTU_RECORTADO_PARTE_{arquivo_idx:02d}.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=(LARGURA_PAGINA, ALTURA_PAGINA))
    print(f"Gerando {nome_arquivo}...")

    for index, row in df.iterrows():
        dados = row.to_dict()
        
        # --- 1. SIMULAÇÃO DE CONTAGEM DE PÁGINAS DESSE CARNÊ ---
        imagens = ["reciboentrega.png", "demonstrativo.png", "observacoes.png"]
        imgs_existentes = [img for img in imagens if os.path.exists(img)]
        qtd_paginas_iniciais = len(imgs_existentes)
        
        # Validar as parcelas normais
        p_validas = []
        for n in range(1, 13):
            v_p = dados.get(f'Valor Total da Parcela {n}')
            if pd.notna(v_p):
                try:
                    if float(str(v_p).replace(',', '.')) > 0:
                        p_validas.append(str(n))
                except: pass
        
        total_p = len(p_validas)
        
        # Validar se terá cota única
        pode_gerar_u = False
        if col_u_total:
            v_u = dados.get(col_u_total)
            try:
                if pd.notna(v_u) and float(str(v_u).replace(',', '.')) > 0:
                    pode_gerar_u = True
            except: pass
            
        qtd_pagina_unica = 1 if (pode_gerar_u and os.path.exists("boletounica.png")) else 0
        
        # O total de parcelas (boletos normais + páginas em branco complementares) será sempre 10 se existirem parcelas.
        qtd_parcelas_impressas = max(10, total_p) if total_p > 0 else 0
        if not os.path.exists("boleto.png"):
            qtd_parcelas_impressas = 0 # Segurança caso não tenha a imagem base do boleto

        paginas_deste_carne = qtd_paginas_iniciais + qtd_pagina_unica + qtd_parcelas_impressas
        
        # --- 2. QUEBRA DE ARQUIVO SE O LIMITE FOR ATINGIDO ---
        if paginas_atuais + paginas_deste_carne > MAX_PAGINAS_POR_ARQUIVO:
            c.save()
            print(f"-> Arquivo {nome_arquivo} salvo com {paginas_atuais} páginas.")
            
            arquivo_idx += 1
            paginas_atuais = 0
            nome_arquivo = f"PRODUCAO_CARNES_IPTU_RECORTADO_PARTE_{arquivo_idx:02d}.pdf"
            c = canvas.Canvas(nome_arquivo, pagesize=(LARGURA_PAGINA, ALTURA_PAGINA))
            print(f"Gerando {nome_arquivo}...")

        # --- 3. DESENHO DO CARNÊ NO PDF ATUAL ---
        for img in imgs_existentes:
            c.drawImage(img, 0, Y_FIXO, width=LARGURA_PAGINA, height=ALTURA_PAGINA)
            if img == "reciboentrega.png": 
                preencher_recibo(c, dados, Y_FIXO)
            elif img == "demonstrativo.png": 
                preencher_demonstrativo(c, dados, Y_FIXO, col_u_venc, col_u_liq)
            c.showPage()
        
        if qtd_pagina_unica > 0:
            c.drawImage("boletounica.png", 0, Y_FIXO, width=LARGURA_PAGINA, height=ALTURA_PAGINA)
            preencher_boleto(c, dados, Y_FIXO, col_u_total, total_p)
            c.showPage()

        for num in p_validas:
            if os.path.exists("boleto.png"):
                c.drawImage("boleto.png", 0, Y_FIXO, width=LARGURA_PAGINA, height=ALTURA_PAGINA)
                preencher_boleto(c, dados, Y_FIXO, num, total_p)
                c.showPage()

        # Completar com páginas em branco se necessário
        if total_p > 0 and total_p < 10:
            paginas_em_branco = 10 - total_p
            for _ in range(paginas_em_branco):
                c.showPage()

        # Soma as páginas desenhadas ao contador do arquivo atual
        paginas_atuais += paginas_deste_carne

    # Salva o último PDF restante ao terminar o loop
    if paginas_atuais > 0:
        c.save()
        print(f"-> Arquivo {nome_arquivo} salvo com {paginas_atuais} páginas.")

    print("\nSucesso! Todos os arquivos foram gerados e divididos perfeitamente.")

except Exception as e:
    print(f"Erro no processamento: {e}")
