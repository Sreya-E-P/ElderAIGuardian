import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      welcome: 'Welcome',
      dashboard: 'Dashboard',
      chat: 'Chat',
      emergency: 'Emergency',
      medication: 'Medication',
      scamDetection: 'Scam Detection',
      wellness: 'Wellness',
      familyPortal: 'Family Portal',
      settings: 'Settings',
      login: 'Login',
      register: 'Register',
      logout: 'Logout',
      profile: 'Profile',
      save: 'Save',
      cancel: 'Cancel',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      search: 'Search',
      filter: 'Filter',
      sort: 'Sort',
      view: 'View',
      download: 'Download',
      upload: 'Upload',
      share: 'Share',
      help: 'Help',
      about: 'About',
      contact: 'Contact',
      privacy: 'Privacy Policy',
      terms: 'Terms of Service',
    },
  },
  es: {
    translation: {
      welcome: 'Bienvenido',
      dashboard: 'Tablero',
      chat: 'Chat',
      emergency: 'Emergencia',
      medication: 'Medicacin',
      scamDetection: 'Deteccin de Fraude',
      wellness: 'Bienestar',
      familyPortal: 'Portal Familiar',
      settings: 'Configuracin',
      login: 'Iniciar Sesin',
      register: 'Registrarse',
      logout: 'Cerrar Sesin',
      profile: 'Perfil',
      save: 'Guardar',
      cancel: 'Cancelar',
      delete: 'Eliminar',
      edit: 'Editar',
      add: 'Agregar',
      search: 'Buscar',
      filter: 'Filtrar',
      sort: 'Ordenar',
      view: 'Ver',
      download: 'Descargar',
      upload: 'Subir',
      share: 'Compartir',
      help: 'Ayuda',
      about: 'Acerca de',
      contact: 'Contacto',
      privacy: 'Poltica de Privacidad',
      terms: 'Trminos de Servicio',
    },
  },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en',
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
