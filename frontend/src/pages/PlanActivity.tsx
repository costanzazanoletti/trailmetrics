import PlanActivityForm from '../components/PlanActivityForm';

const PlanActivity = () => {
  return (
    <div className="container mx-auto p-6 text-gray-700">
      <h1 className="text-2xl font-semibold mb-6">Plan a New Activity</h1>
      <PlanActivityForm />
    </div>
  );
};

export default PlanActivity;
