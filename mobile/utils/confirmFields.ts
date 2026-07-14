/** Smart confirm: only surface fields that need a human check. */

export const CONFIDENCE_THRESHOLD = 0.8;

/** Always editable on confirm (required to save). */
export const ALWAYS_VISIBLE_FIELDS = ['name', 'category'] as const;

/** Empty identity fields are worth a glance on photo/email ingest. */
export const IDENTITY_FIELDS = ['brand', 'material', 'size', 'product_name'] as const;

export const OPTIONAL_CONFIRM_FIELDS = [
  'subcategory',
  'brand',
  'product_name',
  'color',
  'material',
  'size',
  'pattern',
  'formality',
  'occasion',
  'weather_tag',
  'seasons',
] as const;

export type ConfirmField = (typeof ALWAYS_VISIBLE_FIELDS)[number] | (typeof OPTIONAL_CONFIRM_FIELDS)[number];

export type ConfirmFieldValues = Partial<
  Record<ConfirmField, string | string[] | boolean | null | undefined>
>;

function hasValue(value: string | string[] | boolean | null | undefined): boolean {
  if (value == null) return false;
  if (typeof value === 'boolean') return true;
  if (Array.isArray(value)) return value.length > 0;
  return String(value).trim().length > 0;
}

export function fieldNeedsCheck(
  field: ConfirmField,
  confidence: Record<string, number>,
  value: string | string[] | boolean | null | undefined,
  source: string,
): boolean {
  if (source === 'manual') return false;

  const score = confidence[field];
  if (typeof score === 'number') {
    return score < CONFIDENCE_THRESHOLD;
  }

  // No score from the model: trust filled values; flag empty identity for a quick fill.
  if (!hasValue(value)) {
    return (IDENTITY_FIELDS as readonly string[]).includes(field);
  }
  return false;
}

export function fieldsNeedingCheck(
  confidence: Record<string, number>,
  values: ConfirmFieldValues,
  source: string,
): ConfirmField[] {
  if (source === 'manual') return [];
  const fields: ConfirmField[] = [
    ...ALWAYS_VISIBLE_FIELDS,
    ...OPTIONAL_CONFIRM_FIELDS,
  ];
  return fields.filter((field) => fieldNeedsCheck(field, confidence, values[field], source));
}

export function shouldUseSmartConfirm(source: string, editing: boolean): boolean {
  return !editing && source !== 'manual';
}

export function formatAcceptedSummary(values: ConfirmFieldValues, checkFields: ConfirmField[]): string {
  const hiddenFilled: string[] = [];
  const candidates: ConfirmField[] = [
    'color',
    'subcategory',
    'pattern',
    'formality',
    'brand',
    'material',
    'size',
  ];
  for (const field of candidates) {
    if (checkFields.includes(field)) continue;
    const value = values[field];
    if (!hasValue(value)) continue;
    if (Array.isArray(value)) {
      hiddenFilled.push(value.slice(0, 2).join(', '));
    } else {
      hiddenFilled.push(String(value));
    }
  }
  if (!hiddenFilled.length) return '';
  return `Accepted: ${hiddenFilled.slice(0, 5).join(' · ')}`;
}

export function draftLooksSolid(
  confidence: Record<string, number>,
  values: ConfirmFieldValues,
  source: string,
): boolean {
  if (source === 'manual') return false;
  if (!hasValue(values.name) || !hasValue(values.category)) return false;
  // Empty optional identity (brand/size) can still show for a glance, but shouldn't
  // block the "Looks good" path — only explicit low confidence scores do.
  const lowScored = fieldsNeedingCheck(confidence, values, source).filter(
    (field) => typeof confidence[field] === 'number' && confidence[field] < CONFIDENCE_THRESHOLD,
  );
  return lowScored.length === 0;
}
