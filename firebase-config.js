// ============================================================
//  CONFIGURACIÓN DE FIREBASE — App de Propinas La Rusia SPA
// ============================================================
//  Cómo obtener estos datos:
//    1. https://console.firebase.google.com  →  proyecto "larusia-apps"
//    2. ⚙ Configuración del proyecto → "Tus apps" → app web (</>)
//    3. Copiar el objeto firebaseConfig y pegarlo abajo.
//
//  IMPORTANTE — esto NO es una contraseña:
//  la apiKey de Firebase es pública por diseño (viaja en el navegador de
//  cualquiera que abra la página). Lo que protege los datos son las reglas
//  de database.rules.json, no esta clave. Por eso puede vivir en un
//  repositorio público sin problema.
// ============================================================

window.FIREBASE_CONFIG = {
  apiKey:            "AIzaSyBs2LUVSVSWBwuzet8hqAhM4PUOatmDjIo",
  authDomain:        "larusia-apps.firebaseapp.com",
  databaseURL:       "https://larusia-apps-default-rtdb.firebaseio.com",
  projectId:         "larusia-apps",
  storageBucket:     "larusia-apps.firebasestorage.app",
  messagingSenderId: "196879088302",
  appId:             "1:196879088302:web:8d20d5a8cb1ea46737cb3f"
};

// ---------- MANTENCION ----------
// true  = la app queda cerrada: solo entra la administración con su correo.
// false = abierta: los trabajadores entran con su RUT.
// Ojo: este interruptor solo cambia lo que se ve. El bloqueo real está en
// database.rules.json, y los dos se cambian juntos (ver README, punto 4).
window.MANTENIMIENTO = true;

// Correo de la cuenta de administración en Firebase Authentication.
// La contraseña del administrador vive SOLO en Firebase Auth: nunca en la
// base de datos ni en este archivo.
window.ADMIN_EMAIL = "oscar@larusia.app";
