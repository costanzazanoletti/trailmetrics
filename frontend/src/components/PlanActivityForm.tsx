import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPlannedActivity } from '../services/activityService';
import { PlannedActivityInput } from '../types/activity';

const PlanActivityForm = () => {
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [distance, setDistance] = useState('');
  const [elevationGain, setElevationGain] = useState('');
  const [sportType, setSportType] = useState('Run');
  const [plannedDuration, setPlannedDuration] = useState(3600);
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!file) return setError('Please upload a GPX file.');

    const isoStartDate = new Date(`${startDate}T${startTime}:00`).toISOString();

    const data: PlannedActivityInput = {
      name,
      distance: parseFloat(distance),
      planned_duration: plannedDuration,
      total_elevation_gain: parseFloat(elevationGain),
      type: 'planned',
      sport_type: sportType,
      start_date: isoStartDate,
    };

    try {
      await createPlannedActivity(data, file);
      navigate('/planning');
    } catch {
      setError('Submission failed. Please try again.');
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 bg-white p-6 rounded shadow max-w-xl mx-auto"
    >
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div>
        <label className="block mb-1 text-sm font-medium">Activity Name</label>
        <input
          type="text"
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">Distance (m)</label>
        <input
          type="number"
          step="0.01"
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
          value={distance}
          onChange={(e) => setDistance(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">
          Elevation Gain (m)
        </label>
        <input
          type="number"
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
          value={elevationGain}
          onChange={(e) => setElevationGain(e.target.value)}
          required
        />
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">Sport Type</label>
        <select
          value={sportType}
          onChange={(e) => setSportType(e.target.value)}
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
        >
          <option value="Run">Run</option>
          <option value="Trail Run">Trail Run</option>
        </select>
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">
          Planned Duration
        </label>
        <select
          value={plannedDuration}
          onChange={(e) => setPlannedDuration(parseInt(e.target.value))}
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
        >
          {[...Array(48)].map((_, i) => {
            const sec = (i + 1) * 3600;
            return (
              <option key={sec} value={sec}>
                {i + 1} hour{i > 0 ? 's' : ''}
              </option>
            );
          })}
        </select>
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">
          Start Date and Time
        </label>
        <div className="flex gap-4">
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-1/2 p-2 border border-gray-300 rounded bg-gray-50"
            required
          />
          <input
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            className="w-1/2 p-2 border border-gray-300 rounded bg-gray-50"
            required
          />
        </div>
      </div>

      <div>
        <label className="block mb-1 text-sm font-medium">GPX File</label>
        <input
          type="file"
          accept=".gpx"
          className="w-full p-2 border border-gray-300 rounded bg-gray-50"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          required
        />
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={() => navigate('/planning')}
          className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-brand-sage text-white px-4 py-2 rounded hover:bg-brand-sage-dark"
        >
          Submit
        </button>
      </div>
    </form>
  );
};

export default PlanActivityForm;
