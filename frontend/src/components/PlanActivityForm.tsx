import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPlannedActivity } from '../services/activityService';
import { PlannedActivityInput } from '../types/activity';

interface PlanActivityFormProps {
  initialValues?: Partial<PlannedActivityInput>;
  onSubmit?: (data: PlannedActivityInput, file: File) => Promise<void>;
  submitLabel?: string;
  isEditMode?: boolean;
}

const PlanActivityForm = ({
  initialValues = {},
  onSubmit,
  submitLabel = 'Submit',
  isEditMode = false,
}: PlanActivityFormProps) => {
  const navigate = useNavigate();

  const [name, setName] = useState(initialValues.name || '');
  const [distance, setDistance] = useState(
    initialValues.distance ? (initialValues.distance / 1000).toString() : ''
  );
  const [elevationGain, setElevationGain] = useState(
    initialValues.total_elevation_gain?.toString() || ''
  );
  const [sportType, setSportType] = useState(initialValues.sport_type || 'Run');
  const [plannedDuration, setPlannedDuration] = useState(
    initialValues.planned_duration?.toString() || ''
  );
  const [startDate, setStartDate] = useState(
    initialValues.start_date
      ? new Date(initialValues.start_date).toISOString().split('T')[0]
      : ''
  );
  const [startTime, setStartTime] = useState(
    initialValues.start_date
      ? new Date(initialValues.start_date)
          .toISOString()
          .split('T')[1]
          ?.slice(0, 5) || ''
      : ''
  );
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!name.trim()) newErrors.name = 'Activity name is required.';
    if (!plannedDuration)
      newErrors.plannedDuration = 'Please select a planned duration.';
    if (!file && !isEditMode) newErrors.file = 'Please upload a GPX file.';

    const parsedDate = new Date(`${startDate}T${startTime}:00`);
    const now = new Date();
    now.setHours(now.getHours() + 6);
    if (!startDate || !startTime || parsedDate < now) {
      newErrors.startDate =
        'Start date must be at least 6 hours in the future.';
    }

    return newErrors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    const data: PlannedActivityInput = {
      name,
      distance: distance ? parseFloat(distance) * 1000 : 0,
      planned_duration: parseInt(plannedDuration),
      total_elevation_gain: elevationGain ? parseFloat(elevationGain) : 0,
      type: 'planned',
      sport_type: sportType,
      start_date: new Date(`${startDate}T${startTime}:00`).toISOString(),
    };

    try {
      if (onSubmit) {
        await onSubmit(data, file!);
      } else {
        await createPlannedActivity(data, file!);
        navigate('/planning');
      }
    } catch {
      setErrors({ form: 'Submission failed. Please try again.' });
    }
  };

  const inputClass = (field: string) =>
    `w-full p-2 border rounded bg-gray-50 ${
      errors[field] ? 'border-red-500' : 'border-gray-300'
    }`;

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-white p-6 rounded shadow max-w-xl mx-auto"
    >
      {errors.form && <p className="text-red-600 text-sm">{errors.form}</p>}

      <div>
        <label className="block mb-1 text-sm font-medium">
          Activity Name *
        </label>
        <input
          type="text"
          className={inputClass('name')}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {errors.name && (
          <p className="text-red-500 text-sm mt-1">{errors.name}</p>
        )}
      </div>

      <div className="flex gap-4">
        <div className="w-1/3">
          <label className="block mb-1 text-sm font-medium">
            Distance (km)
          </label>
          <input
            type="number"
            step="0.01"
            className={inputClass('distance')}
            value={distance}
            onChange={(e) => setDistance(e.target.value)}
          />
        </div>

        <div className="w-1/3">
          <label className="block mb-1 text-sm font-medium">
            Elevation Gain (D± m)
          </label>
          <input
            type="number"
            className={inputClass('elevationGain')}
            value={elevationGain}
            onChange={(e) => setElevationGain(e.target.value)}
          />
        </div>

        <div className="w-1/3">
          <label className="block mb-1 text-sm font-medium">
            Planned Duration *
          </label>
          <select
            value={plannedDuration}
            onChange={(e) => setPlannedDuration(e.target.value)}
            className={inputClass('plannedDuration')}
          >
            <option value="">Select duration</option>
            {[...Array(48)].map((_, i) => {
              const sec = (i + 1) * 3600;
              return (
                <option key={sec} value={sec}>
                  {i + 1} hour{i > 0 ? 's' : ''}
                </option>
              );
            })}
          </select>
          {errors.plannedDuration && (
            <p className="text-red-500 text-sm mt-1">
              {errors.plannedDuration}
            </p>
          )}
        </div>
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">Sport Type</label>
        <div className="flex gap-4">
          <label className="inline-flex items-center">
            <input
              type="radio"
              value="Run"
              checked={sportType === 'Run'}
              onChange={(e) => setSportType(e.target.value)}
              className="mr-2"
            />
            Run
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              value="Trail Run"
              checked={sportType === 'Trail Run'}
              onChange={(e) => setSportType(e.target.value)}
              className="mr-2"
            />
            Trail Run
          </label>
        </div>
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">
          Start Date and Time *
        </label>
        <div className="flex gap-4">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className={`w-1/2 p-2 rounded bg-gray-50 ${
              errors.startDate ? 'border-red-500' : 'border-gray-300 border'
            }`}
          />
          <input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className={`w-1/2 p-2 rounded bg-gray-50 ${
              errors.startDate ? 'border-red-500' : 'border-gray-300 border'
            }`}
          />
        </div>
        {errors.startDate && (
          <p className="text-red-500 text-sm mt-1">{errors.startDate}</p>
        )}
      </div>

      {!isEditMode && (
        <div>
          <label className="block mb-1 text-sm font-medium">GPX File *</label>
          <input
            type="file"
            accept=".gpx"
            className={inputClass('file')}
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          {errors.file && (
            <p className="text-red-500 text-sm mt-1">{errors.file}</p>
          )}
        </div>
      )}

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={() => navigate('/planning')}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-brand-sage text-white px-4 py-2 rounded hover:bg-brand-sage-dark cursor-pointer"
        >
          {submitLabel}
        </button>
      </div>
    </form>
  );
};

export default PlanActivityForm;
