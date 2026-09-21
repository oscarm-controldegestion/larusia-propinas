# App de Propinas y Consumos — La Rusia SPA

Aplicación web donde cada trabajador revisa **sus propinas** (bruta, retención
del 6 %, depositado y saldo del fondo) y **su consumo interno** del mes.
La administración carga los datos una vez al mes.

- **Dirección pública:** https://oscarm-controldegestion.github.io/larusia-propinas/
- **Base de datos:** Firebase Realtime Database (plan gratuito Spark)
- **Hosting:** GitHub Pages (gratuito)
- **Costo mensual:** $0

---

## 1. Cómo entra cada quien

| Quién | Usuario | Contraseña |
|---|---|---|
| Trabajador | su RUT (con o sin puntos) | su RUT sin puntos ni guion, la primera vez |
| Administración | su RUT | la que cada uno fijó en Firebase Authentication |

En su primer ingreso la app **obliga** al trabajador a cambiar la clave.
Si alguien la olvida: pestaña **Claves → Restablecer**; vuelve a quedar su RUT.

---

## 2. Proceso mensual — día 6

1. Cerrar el `INFORME PERSONAL <MES> <AÑO>.xlsx` del mes en
   `VARIABLES MENSUALES\<MES> <AÑO>\`.
2. Entrar a la app como administración → pestaña **Importar**.
3. Arrastrar la planilla. La app acepta cualquier columna que contenga:

   | Se busca | Columna típica del informe |
   |---|---|
   | `rut` | Rut |
   | `nombre` / `trabajador` | Trabajador |
   | `mes` | (si no está, agregar una columna con "Agosto 2026") |
   | `inicial` o `propina` | PROPINAS |
   | `fondo`, `6%` o `retenci` | 6% DESCUENTO |
   | `pagada`, `neto` o `deposito` | PROPINAS NETAS |

4. Revisar la vista previa y confirmar. Los meses ya cargados se
   **reemplazan**, no se duplican.
5. Pestaña **Consumo** → cargar el detalle de consumo no pagado del mes.
6. Ejecutar el respaldo (punto 5 de este documento).

> El total de propinas del mes debe cuadrar con el reporte de Fudo. El reparto
> entre trabajadores lo hace la supervisión y se ingresa en las variables
> mensuales; la app solo refleja ese reparto.

---

## 3. Puesta en marcha (una sola vez)

### 3.1 El proyecto de Firebase

La app vive en el proyecto **`larusia-apps`**, el mismo que ya usaban otras
aplicaciones de La Rusia. Su base de datos tiene tres ramas independientes:

| Rama | De quién es |
|---|---|
| `propinas` | esta app |
| `apps`, `ricopan` | otras aplicaciones; las reglas las dejan cerradas, igual que antes |

Lo que quedó configurado (20/09/2026):

1. **Authentication → Método de acceso →** Correo electrónico/contraseña: **habilitado**.
2. **Authentication → Configuración → Acciones del usuario →** "Habilitar la
   creación (registro)": **apagado**. Nadie puede crearse una cuenta; las crea
   la administración desde la consola.
3. **Authentication → Users → Agregar usuario**, con la contraseña que elija
   cada uno (no son correos reales, solo identifican la cuenta):
   - `oscar@larusia.app`
   - `rossana@larusia.app`
   - `paola@larusia.app`
   - `carga@larusia.app` — la usa la carga automática del día 6
4. **Realtime Database → Reglas:** publicadas las de `database.rules.json`.

> Al abrir la app a los trabajadores hay que volver a **encender** "Habilitar la
> creación (registro)" y habilitar el proveedor **Anónimo**: la app abre una
> sesión anónima para poder validar el RUT antes de mostrar nada.

### 3.2 `firebase-config.js`

Ya trae la configuración real de `larusia-apps`.
Esa `apiKey` **no es un secreto**: es pública por diseño y viaja en el
navegador de cualquiera que abra la página. Lo que protege los datos son las
reglas, no la clave.

### 3.3 Cargar los datos históricos

```
python generar_carga_inicial.py
```

Genera `carga_inicial.json` con los 39 trabajadores desde octubre 2025.

**Ojo:** la base ya trae el nodo `propinas` de la versión original de la app.
No se importa encima sin comparar antes: importar en el nodo raíz **reemplaza**
lo que haya. Lo que corresponde es cargar solo los meses que falten, con
`propinas_cargar_mes.py` mes por mes.

### 3.4 Publicar las reglas

Opción A — consola: **Realtime Database → Reglas** → pegar el contenido de
`database.rules.json` (sin los comentarios `//`) → **Publicar**.

Opción B — línea de comandos:

```
npm install -g firebase-tools
firebase login
firebase deploy --only database --project larusia-apps
```

### 3.5 Verificar

Abrir la app en una ventana de incógnito y entrar con un RUT de prueba.

---

## 4. Modo mantención (cerrar y abrir la app)

Mientras se revisa la información, la app queda **cerrada para los trabajadores**:
la página muestra un aviso y solo entra la administración con su correo.

El bloqueo de verdad lo hace Firebase, no la página: con las reglas de mantención
publicadas, quien no tenga una cuenta de administración **no obtiene ni un dato**,
aunque conozca la dirección o abra la consola del navegador.

| Estado | `firebase-config.js` | Reglas publicadas |
|---|---|---|
| Cerrada (actual) | `window.MANTENIMIENTO = true` | `database.rules.json` |
| Abierta | `window.MANTENIMIENTO = false` | `database.rules.abierta.json` |

**Los dos cambios van juntos.** Si se abre solo la página, las reglas siguen
bloqueando y los trabajadores verán un error al entrar; si se abren solo las
reglas, la página seguirá mostrando el aviso.

Para abrir cuando terminen de revisar:

```
# 1. en firebase-config.js: window.MANTENIMIENTO = false   (y publicar el cambio)
# 2. publicar las reglas abiertas:
copy database.rules.abierta.json database.rules.json
firebase deploy --only database --project larusia-apps
```

Y en la consola de Firebase, dos interruptores que hoy están apagados a propósito:
**Authentication → Método de acceso →** habilitar **Anónimo**, y
**Authentication → Configuración → Acciones del usuario →** encender
"Habilitar la creación (registro)". Sin eso la app abierta no puede abrir la
sesión anónima que necesita para validar el RUT.

O, desde la consola: **Realtime Database → Reglas** → pegar el contenido de
`database.rules.abierta.json` → **Publicar**.

Durante la mantención la administración entra con su **correo**
(`oscar@larusia.app`, etc.), no con su RUT.

---

## 5. Seguridad

Qué protege cada cosa:

| Riesgo | Cómo está cubierto |
|---|---|
| Que alguien lea la base sin pasar por la app | Las reglas exigen sesión iniciada |
| Que un trabajador altere propinas o consumos | Solo escriben las tres cuentas de administración y la de carga automática |
| Que se filtren las contraseñas | La base guarda solo `SHA-256("RUT:clave")`; nadie —ni la administración— puede leerlas |
| Que alguien se haga pasar por administrador | La lista de correos con permiso de escritura es fija en las reglas y el registro público está apagado |

**Lo que todavía queda abierto, dicho derecho:** la app abre una sesión
*anónima* para poder validar el RUT antes de mostrar nada, así que cualquiera
que tenga la dirección de la página puede leer los nombres, RUT y montos de
propinas. No puede modificar nada ni obtener contraseñas, pero puede mirar.

Cerrar eso del todo exige que cada trabajador tenga cuenta propia en Firebase
Authentication, y entonces una clave olvidada solo se recupera por correo
—que los trabajadores no tienen registrado—. Se eligió a conciencia la opción
operable. Si más adelante se recogen los correos del personal, la app puede
pasar a cuentas individuales y cerrar también la lectura.

---

## 6. Respaldos

```
python respaldo_firebase.py
```

Deja `propinas_AAAAMMDD_HHMM.json` y un `.xlsx` legible en
`...\PROPINAS MENSUALES\RESPALDOS\`, y conserva los últimos 30.
No necesita ninguna clave: usa la configuración pública de la app.

Conviene dejarlo como tarea programada semanal. **La base gratuita de Firebase
no tiene respaldo automático**: si se borra algo por error, el único camino de
vuelta es uno de estos archivos.

---

## 7. Archivos del repositorio

| Archivo | Para qué |
|---|---|
| `index.html` | La aplicación completa (una sola página) |
| `firebase-config.js` | Configuración pública + interruptor de mantención |
| `database.rules.json` | Reglas activas (hoy: mantención, solo administración) |
| `database.rules.abierta.json` | Reglas para cuando se abra a los trabajadores |
| `firebase.json`, `.firebaserc` | Configuración del CLI y del emulador local |
| `generar_carga_inicial.py` | Arma la carga inicial desde las planillas |
| `respaldo_firebase.py` | Respaldo periódico |

### Probar cambios sin tocar la base real

```
firebase emulators:start --only auth,database,hosting
```

Levanta una copia local en http://127.0.0.1:5050 con su propia base vacía.

---

## 8. Historial

- **sep-2026** — Se migró de Supabase a Firebase. El proyecto de Supabase
  (plan gratuito) se dio de baja por inactividad y se perdió el acceso a los
  datos; la app quedó respondiendo "RUT o contraseña incorrectos" a todo el
  mundo. En la migración se corrigieron además dos cosas serias: la base era
  **de lectura y escritura pública** y las contraseñas se guardaban **en texto
  plano**, visibles en la pestaña Claves.
