# -*- coding: utf-8 -*-
"""
Respaldo de la base de datos de la app de propinas.

Descarga todo el nodo /propinas y lo deja en la carpeta de propinas de
La Rusia, con fecha y hora. Tambien escribe un .xlsx legible para revisar
los montos sin abrir el JSON.

Para leer necesita una cuenta: las reglas no dejan leer sin sesion. Usa la
seccion "firebase_propinas" de claves.enc (cuenta carga@larusia.app); nunca
imprime las credenciales. Si esa seccion no existe y el registro anonimo esta
habilitado, cae a una sesion anonima.

Uso:
    python respaldo_firebase.py                 # respaldo normal
    python respaldo_firebase.py --carpeta "D:\\otra\\ruta"
    python respaldo_firebase.py --conservar 60  # cuantos respaldos guardar
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

CONFIG_WEB = 'https://oscarm-controldegestion.github.io/larusia-propinas/firebase-config.js'

# La apiKey del proyecto esta restringida por dominio de origen. Un script no
# manda "Referer", asi que Google lo rechaza con "Requests from referer <empty>
# are blocked". Se manda el del sitio publicado, que es de donde sale la app.
REFERER = 'https://oscarm-controldegestion.github.io/larusia-propinas/'

CARPETA_DEFECTO = (r'C:\Users\oscar\Mi unidad (oscar.munizaga@gmail.com)\PERSONAL\GEST'
                   r'\CONTABILIDAD GEST\1.- CLIENTES ACTIVOS\LA RUSIA\RECURSOS HUMANOS'
                   r'\VARIABLES MENSUALES\PROPINAS MENSUALES\RESPALDOS')


def leer_config():
    """Toma apiKey y databaseURL de firebase-config.js (web o copia local)."""
    texto = None
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'firebase-config.js')
    for origen in (CONFIG_WEB, os.path.abspath(local)):
        try:
            if origen.startswith('http'):
                with urllib.request.urlopen(origen, timeout=20) as r:
                    texto = r.read().decode('utf-8')
            else:
                with open(origen, encoding='utf-8') as fh:
                    texto = fh.read()
            break
        except Exception:
            continue
    if not texto:
        raise SystemExit('No se pudo leer firebase-config.js')

    def campo(nombre):
        m = re.search(nombre + r'\s*:\s*"([^"]+)"', texto)
        return m.group(1) if m else None

    api = campo('apiKey')
    url = campo('databaseURL')
    if not api or not url or 'PENDIENTE' in api:
        raise SystemExit('firebase-config.js todavia no tiene la configuracion real.')
    return api, url.rstrip('/')


def _post(url, cuerpo):
    req = urllib.request.Request(
        url, data=json.dumps(cuerpo).encode(),
        headers={'Content-Type': 'application/json', 'Referer': REFERER})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def sesion(api_key):
    """Las reglas exigen sesion iniciada para leer. Primero la cuenta de carga."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '..', '..', 'scripts'))
        import claves_lib
        c = claves_lib.cargar('firebase_propinas')
    except Exception:
        c = None
    if c and c.get('email') and c.get('password'):
        try:
            r = _post('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=' + api_key,
                      {'email': c['email'], 'password': c['password'], 'returnSecureToken': True})
            return r['idToken']
        except urllib.error.HTTPError:
            raise SystemExit('LOGIN FALLIDO en Firebase con la cuenta de carga. No se reintenta.')
    try:
        return _post('https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=' + api_key,
                     {'returnSecureToken': True})['idToken']
    except urllib.error.HTTPError as e:
        raise SystemExit('No hay como iniciar sesion para leer la base (HTTP %s). '
                         'Agrega la seccion "firebase_propinas" a claves.json '
                         '(email y password de carga@larusia.app) y pide "cifra las claves".' % e.code)


def escribir_xlsx(datos, destino):
    try:
        import openpyxl
    except ImportError:
        return None
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'PROPINAS'
    ws.append(['RUT', 'TRABAJADOR', 'MES', 'PROPINA BRUTA', 'RETENCION 6%',
               'PROPINA PAGADA', 'COMPENSACION', 'TOTAL RECIBIDO', 'SALDO FONDO'])
    for rut, w in sorted((datos.get('workers') or {}).items()):
        for h in w.get('h', []):
            ws.append([rut, w.get('n', ''), h.get('m', ''), h.get('p', 0), h.get('r', 0),
                       h.get('net', 0), h.get('c', 0), h.get('nf', 0), h.get('s', 0)])
    ws2 = wb.create_sheet('CONSUMO')
    ws2.append(['RUT', 'TRABAJADOR', 'MES', 'DETALLE', 'MONTO'])
    for rut, c in sorted((datos.get('consumo') or {}).items()):
        for h in c.get('h', []):
            for it in h.get('items', []):
                ws2.append([rut, c.get('n', ''), h.get('m', ''),
                            it.get('det', ''), it.get('monto', 0)])
    for hoja in (ws, ws2):
        for col in hoja.columns:
            ancho = max((len(str(c.value)) for c in col if c.value is not None), default=8)
            hoja.column_dimensions[col[0].column_letter].width = min(38, ancho + 2)
        hoja.freeze_panes = 'A2'
    wb.save(destino)
    return destino


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--carpeta', default=CARPETA_DEFECTO)
    ap.add_argument('--conservar', type=int, default=30)
    args = ap.parse_args()

    api, url = leer_config()
    token = sesion(api)
    with urllib.request.urlopen(url + '/propinas.json?auth=' + token, timeout=120) as r:
        datos = json.loads(r.read())
    if not datos:
        raise SystemExit('La base respondio vacia: no se escribe respaldo (para no tapar uno bueno).')

    os.makedirs(args.carpeta, exist_ok=True)
    sello = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    ruta_json = os.path.join(args.carpeta, 'propinas_%s.json' % sello)
    with open(ruta_json, 'w', encoding='utf-8') as fh:
        json.dump(datos, fh, ensure_ascii=False, indent=1)
    ruta_xlsx = escribir_xlsx(datos, os.path.join(args.carpeta, 'propinas_%s.xlsx' % sello))

    nw = len(datos.get('workers') or {})
    nm = len({h['m'] for w in (datos.get('workers') or {}).values() for h in w.get('h', [])})
    total = sum(h.get('p', 0) for w in (datos.get('workers') or {}).values()
                for h in w.get('h', []))
    print('Respaldo OK: %d trabajadores, %d meses, $%s en propinas'
          % (nw, nm, format(int(total), ',d').replace(',', '.')))
    print('   %s' % ruta_json)
    if ruta_xlsx:
        print('   %s' % ruta_xlsx)

    # Conservar solo los ultimos N
    viejos = sorted(f for f in os.listdir(args.carpeta)
                    if f.startswith('propinas_') and f.endswith('.json'))
    for f in viejos[:-args.conservar]:
        for ext in ('.json', '.xlsx'):
            try:
                os.remove(os.path.join(args.carpeta, f[:-5] + ext))
            except OSError:
                pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
