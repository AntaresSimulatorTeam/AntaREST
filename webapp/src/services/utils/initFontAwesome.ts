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
} from '@fortawesome/free-solid-svg-icons';

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
  );
}
