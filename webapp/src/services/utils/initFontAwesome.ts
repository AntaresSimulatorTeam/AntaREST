import { library } from '@fortawesome/fontawesome-svg-core';
import {
  faGithub,
} from '@fortawesome/free-brands-svg-icons';
import {
  faUser,
  faClock,
  faHistory,
  faCodeBranch,
  faFileAlt,
  faFileCode,
  faCalendarCheck,
  faCalendar,
  faUserCircle,
  faEdit,
  faShieldAlt,
  faUsers,
  faBolt,
} from '@fortawesome/free-solid-svg-icons';
import { faQuestionCircle, faCopy } from '@fortawesome/free-regular-svg-icons';

export default function (): void {
  library.add(
    faUser,
    faClock,
    faHistory,
    faCodeBranch,
    faGithub,
    faFileAlt,
    faFileCode,
    faCalendarCheck,
    faCalendar,
    faUserCircle,
    faEdit,
    faShieldAlt,
    faUsers,
    faQuestionCircle,
    faCopy,
    faBolt,
  );
}
