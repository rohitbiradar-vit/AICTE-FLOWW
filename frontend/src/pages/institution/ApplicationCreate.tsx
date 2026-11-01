import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { apiRequest } from '../../api/client';
import { useNavigate, Link } from 'react-router-dom';
import { FilePlus, ArrowLeft } from 'lucide-react';

interface ApplicationFormData {
  academic_year: string;
  application_type: string;
  declared_land_acres: string;
  declared_builtup_sqm: string;
  declared_intake: number;
  declared_faculty_count: number;
  program_name: string;
}

export const ApplicationCreate: React.FC = () => {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<ApplicationFormData>({
    defaultValues: {
      academic_year: '2026-2027',
      application_type: 'EXTENSION_OF_APPROVAL',
      declared_land_acres: '5.0',
      declared_builtup_sqm: '8500',
      declared_intake: 480,
      declared_faculty_count: 45,
      program_name: 'B.Tech / M.Tech in Engineering Disciplines'
    }
  });

  const onSubmit = async (values: ApplicationFormData) => {
    setServerError('');
    setSubmitting(true);
    try {
      const res = await apiRequest('/applications', {
        method: 'POST',
        body: JSON.stringify({
          academic_year: values.academic_year,
          application_type: values.application_type,
          declared_land_acres: values.declared_land_acres,
          declared_builtup_sqm: values.declared_builtup_sqm,
          declared_intake: Number(values.declared_intake),
          declared_faculty_count: Number(values.declared_faculty_count),
          application_data: { program_name: values.program_name }
        })
      });
      navigate(`/institution/applications/${res.id}`);
    } catch (err: any) {
      setServerError(err.message || 'Failed to create application.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Back button */}
      <div>
        <Link to="/institution/applications" className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center gap-1.5">
          <ArrowLeft className="w-4 h-4" /> Back to Applications List
        </Link>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
          <div className="p-2.5 bg-blue-100 text-blue-800 rounded-xl">
            <FilePlus className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">Initiate AICTE Approval Application</h1>
            <p className="text-xs text-slate-500">
              Create a statutory application draft under AICTE Approval Process Handbook (APH 2026-27).
            </p>
          </div>
        </div>

        {serverError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs">
            {serverError}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Academic Year</label>
              <select
                {...register('academic_year', { required: 'Academic year is required' })}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
              >
                <option value="2026-2027">2026-2027</option>
                <option value="2027-2028">2027-2028</option>
              </select>
              {errors.academic_year && <p className="text-[11px] text-red-600 mt-1">{errors.academic_year.message}</p>}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Application Type</label>
              <select
                {...register('application_type', { required: 'Application type is required' })}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
              >
                <option value="EXTENSION_OF_APPROVAL">Extension of Approval (EoA)</option>
                <option value="NEW_INSTITUTE">Establishment of New Technical Institute</option>
                <option value="INCREASE_INTAKE">Increase in Intake / Additional Course</option>
                <option value="CLOSURE_OF_COURSE">Closure of Course / Institute</option>
              </select>
              {errors.application_type && <p className="text-[11px] text-red-600 mt-1">{errors.application_type.message}</p>}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Approved Programs / Disciplines</label>
            <input
              type="text"
              {...register('program_name', { required: 'Program name is required' })}
              placeholder="e.g. B.Tech Computer Science, Artificial Intelligence & Machine Learning"
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg"
            />
            {errors.program_name && <p className="text-[11px] text-red-600 mt-1">{errors.program_name.message}</p>}
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-4">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Statutory Infrastructure & Academic Declarations
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Declared Land Area (in Acres)
                </label>
                <input
                  type="text"
                  {...register('declared_land_acres', { required: 'Land area is required' })}
                  placeholder="e.g. 5.0"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                />
                {errors.declared_land_acres && <p className="text-[11px] text-red-600 mt-1">{errors.declared_land_acres.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Declared Built-up Area (in Sq.Meters)
                </label>
                <input
                  type="text"
                  {...register('declared_builtup_sqm', { required: 'Built-up area is required' })}
                  placeholder="e.g. 8500"
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                />
                {errors.declared_builtup_sqm && <p className="text-[11px] text-red-600 mt-1">{errors.declared_builtup_sqm.message}</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Sanctioned Total Student Intake
                </label>
                <input
                  type="number"
                  {...register('declared_intake', { required: 'Intake is required', min: 30 })}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                />
                {errors.declared_intake && <p className="text-[11px] text-red-600 mt-1">Minimum sanctioned intake is 30</p>}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Total Regular Faculty Members
                </label>
                <input
                  type="number"
                  {...register('declared_faculty_count', { required: 'Faculty count is required', min: 5 })}
                  className="w-full text-xs p-2.5 border border-slate-300 rounded-lg bg-white"
                />
                {errors.declared_faculty_count && <p className="text-[11px] text-red-600 mt-1">Minimum faculty members is 5</p>}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-3">
            <Link
              to="/institution/applications"
              className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold shadow-md cursor-pointer"
            >
              {submitting ? 'Creating Draft...' : 'Create Application Draft'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
