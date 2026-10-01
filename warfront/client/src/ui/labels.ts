import type { DiploState, ResourceKind, UnitStatus } from '@warfront/shared';

/** Korean display names for enum values coming from the server. */
export const STATUS_KO: Record<UnitStatus, string> = {
  IDLE: '대기',
  MOVING: '이동 중',
  ATTACKING: '공격 중',
  DEFENDING: '방어 중',
  RETREATING: '후퇴 중',
  DESTROYED: '전멸',
};

export const RELATION_KO: Record<DiploState, string> = {
  WAR: '전쟁',
  PEACE: '평화',
  ALLIANCE: '동맹',
};

export const RESOURCE_KO: Record<ResourceKind, string> = {
  GRAIN: '곡물',
  IRON: '철',
  COAL: '석탄',
  TIMBER: '목재',
  HORSES: '말',
  WINE: '포도주',
};
