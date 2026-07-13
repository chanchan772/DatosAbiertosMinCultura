// Producción (GitHub Pages): SPA estática. Las funciones de IA (interpretación y
// consultas en lenguaje natural) llaman a DeepSeek DIRECTAMENTE desde el navegador
// (DeepSeek permite CORS). La llave se incluye a propósito para que la demo pública
// funcione sin backend, tal como pidió el equipo.
export const environment = {
  staticMode: true,
  apiBase: '',
  deepseekApiKey: 'sk-31382fc441eb4fe28414478ac6fd793f',
  deepseekUrl: 'https://api.deepseek.com',
  deepseekModel: 'deepseek-chat',
};
