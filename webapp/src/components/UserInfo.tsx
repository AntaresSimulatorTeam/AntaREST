import React from 'react';
import { UserDTO } from '../services/api/user';

interface PropTypes {
  user: UserDTO;
}

// Composant simple ici
// a noter que lorsque le composant est compliqué ou contient des sous composants propre
// on aura un directory avec un index.tsx à la racine à la place d'un unique fichier
// on pourra mettre notamment dans ce directory un style.css si besoin de css compliqué (exemple PulsingDot)
// ou d'autres sous composants (StudyCreationTools)
// ou bien du code business extrait de la classe pour plus de lisibilité (fichier.ts au lieu de tsx pour du code qui n'utilise pas react)

const UserInfo = (props: PropTypes) => {
  const { user } = props;

  return (
    <div>
      {user.name}
    </div>
  );
};

export default UserInfo;