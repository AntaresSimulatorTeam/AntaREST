import { StudyMetadata } from "../../../../../../../../common/types";
import client from "../../../../../../../../services/api/client";

interface PlaylistColumns extends Record<string, boolean | number> {
  status: boolean;
  weight: number;
}

export type PlaylistData = Record<number, PlaylistColumns>;

export const DEFAULT_WEIGHT = 1;

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/playlist_form_data`;
}

export async function getPlaylist(
  studyId: StudyMetadata["id"]
): Promise<PlaylistData> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setPlaylist(
  studyId: StudyMetadata["id"],
  data: PlaylistData
): Promise<void> {
  return client.put(makeRequestURL(studyId), data);
}
