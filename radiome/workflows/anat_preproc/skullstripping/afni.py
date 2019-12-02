import nipype.interfaces.utility as util
import nipype.pipeline.engine as pe
from nipype.interfaces import afni
from voluptuous import Schema, In, MultipleInvalid

from radiome.resource_pool import ResourcePool, Resource


# TODO inconsistent type from workflow input
def create_3d_skullstrip_arg_string(shrink_fac: float, var_shrink_fac: bool,
                                    shrink_fac_bot_lim: float, avoid_vent: bool, niter: float,
                                    pushout: bool, touchup: bool, fill_hole: float, avoid_eyes: bool,
                                    use_edge: bool, exp_frac: float, smooth_final: float,
                                    push_to_edge: bool, use_skull: bool, perc_int: float,
                                    max_inter_iter: float, blur_fwhm: float, fac: float, monkey: bool) -> str:
    """
    Method to return option string for 3dSkullStrip

    Parameters
    ----------
    shrink_fac : float
        Parameter controlling the brain vs non-brain intensity threshold (tb)

    var_shrink_fac : boolean
        Vary the shrink factor with the number of iterations

    shrink_fac_bot_lim : float
        Do not allow the varying SF to go below SFBL

    avoid_vent : boolean
        Avoid ventricles

    niter : float
        Number of iterations

    pushout : boolean
        Consider values above each node in addition to values below the node when deciding on expansion

    touchup : boolean
        Perform touchup operations at end to include areas not covered by surface expansion

    fill_hole : float
         Fill small holes that can result from small surface intersections caused by the touchup operation

    avoid_eyes : boolean
        Avoid eyes

    use_edge : boolean
        Use edge detection to reduce leakage into meninges and eyes

    exp_frac : float
        Speed of expansion

    smooth_final : float
        Perform final surface smoothing after all iterations

    push_to_edge : boolean
        Perform aggressive push to edge at the end

    use_skull : boolean
        Use outer skull to limit expansion of surface into the skull due to very strong shading artifacts

    perc_int : float
        Percentage of segments allowed to intersect surface

    max_inter_iter : float
        Number of iteration to remove intersection problems

    blur_fwhm : float
        Blur dset after spatial normalization

    fac : float
         Multiply input dataset by FAC if range of values is too small

    monkey : boolean
        Use monkey option in SkullStripping

    Returns
    -------
    opt_str : string
        Command args

    """

    expr = ''
    defaults = dict(
        fill_hole=10 if touchup else 0,
        shrink_fac=0.6,
        shrink_fac_bot_lim=0.4 if use_edge else 0.65,
        niter=250,
        exp_frac=0.1,
        smooth_final=20,
        perc_int=0,
        max_inter_iter=4,
        blur_fwhm=0,
        fac=1.0,
        monkey=False
    )

    if float(shrink_fac) != defaults['shrink_fac']:
        expr += ' -shrink_fac {0}'.format(shrink_fac)

    if not var_shrink_fac:
        expr += ' -no_var_shrink_fac'

    if monkey:
        expr += ' -monkey'

    if float(shrink_fac_bot_lim) != defaults['shrink_fac_bot_lim']:
        expr += ' -shrink_fac_bot_lim {0}'.format(shrink_fac_bot_lim)

    if not use_edge:
        expr += ' -no_use_edge'

    if not avoid_vent:
        expr += ' -no_avoid_vent'

    if int(niter) != defaults['niter']:
        expr += ' -niter {0}'.format(niter)

    if not pushout:
        expr += ' -no_pushout'

    if not touchup:
        expr += ' -no_touchup'

    if int(fill_hole) != defaults['fill_hole']:
        expr += ' -fill_hole {0}'.format(fill_hole)

    if not avoid_eyes:
        expr += ' -no_avoid_eyes'

    if float(exp_frac) != defaults['exp_frac']:
        expr += ' -exp_frac {0}'.format(exp_frac)

    if int(smooth_final) != defaults['smooth_final']:
        expr += ' -smooth_final {0}'.format(smooth_final)

    if push_to_edge:
        expr += ' -push_to_edge'

    if use_skull:
        expr += ' -use_skull'

    if float(perc_int) != defaults['perc_int']:
        expr += ' -perc_int {0}'.format(perc_int)

    if int(max_inter_iter) != defaults['max_inter_iter']:
        expr += ' -max_inter_iter {0}'.format(max_inter_iter)

    if float(blur_fwhm) != defaults['blur_fwhm']:
        expr += ' -blur_fwhm {0}'.format(blur_fwhm)

    if float(fac) != defaults['fac']:
        expr += ' -fac {0}'.format(fac)

    return expr


def create_workflow() -> pe.Workflow:
    workflow = pe.Workflow(name='skullstrip_afni')

    input_node = pe.Node(util.IdentityInterface(fields=['in_file']), name='input_spec')
    output_node = pe.Node(util.IdentityInterface(fields=['out_file', 'brain_mask', 'brain']), name='output_spec')

    afni_input = pe.Node(util.IdentityInterface(fields=['shrink_factor',
                                                        'var_shrink_fac',
                                                        'shrink_fac_bot_lim',
                                                        'avoid_vent',
                                                        'niter',
                                                        'pushout',
                                                        'touchup',
                                                        'fill_hole',
                                                        'avoid_eyes',
                                                        'use_edge',
                                                        'exp_frac',
                                                        'smooth_final',
                                                        'push_to_edge',
                                                        'use_skull',
                                                        'perc_int',
                                                        'max_inter_iter',
                                                        'blur_fwhm',
                                                        'fac',
                                                        'monkey']),
                         name='AFNI_options')

    skullstrip_args = pe.Node(util.Function(input_names=['spat_norm',
                                                         'spat_norm_dxyz',
                                                         'shrink_fac',
                                                         'var_shrink_fac',
                                                         'shrink_fac_bot_lim',
                                                         'avoid_vent',
                                                         'niter',
                                                         'pushout',
                                                         'touchup',
                                                         'fill_hole',
                                                         'avoid_eyes',
                                                         'use_edge',
                                                         'exp_frac',
                                                         'smooth_final',
                                                         'push_to_edge',
                                                         'use_skull',
                                                         'perc_int',
                                                         'max_inter_iter',
                                                         'blur_fwhm',
                                                         'fac',
                                                         'monkey'],
                                            output_names=['expr'],
                                            function=create_3d_skullstrip_arg_string),
                              name='anat_skullstrip_args')

    workflow.connect([
        (afni_input, skullstrip_args, [
            ('shrink_factor', 'shrink_fac'),
            ('var_shrink_fac', 'var_shrink_fac'),
            ('shrink_fac_bot_lim', 'shrink_fac_bot_lim'),
            ('avoid_vent', 'avoid_vent'),
            ('niter', 'niter'),
            ('pushout', 'pushout'),
            ('touchup', 'touchup'),
            ('fill_hole', 'fill_hole'),
            ('avoid_eyes', 'avoid_eyes'),
            ('use_edge', 'use_edge'),
            ('exp_frac', 'exp_frac'),
            ('smooth_final', 'smooth_final'),
            ('push_to_edge', 'push_to_edge'),
            ('use_skull', 'use_skull'),
            ('perc_int', 'perc_int'),
            ('max_inter_iter', 'max_inter_iter'),
            ('blur_fwhm', 'blur_fwhm'),
            ('fac', 'fac'),
            ('monkey', 'monkey')
        ])
    ])

    anat_skullstrip = pe.Node(interface=afni.SkullStrip(),
                              name='anat_skullstrip')

    anat_skullstrip.inputs.outputtype = 'NIFTI_GZ'

    workflow.connect(input_node, 'in_file',
                     anat_skullstrip, 'in_file')
    workflow.connect(skullstrip_args, 'expr',
                     anat_skullstrip, 'args')
    workflow.connect(anat_skullstrip, 'out_file',
                     output_node, 'out_file')

    # Apply skull-stripping step mask to original volume
    anat_skullstrip_orig_vol = pe.Node(interface=afni.Calc(),
                                       name='anat_skullstrip_orig_vol')

    anat_skullstrip_orig_vol.inputs.expr = 'a*step(b)'
    anat_skullstrip_orig_vol.inputs.outputtype = 'NIFTI_GZ'
    workflow.connect(input_node, 'in_file',
                     anat_skullstrip_orig_vol, 'in_file_a')

    anat_brain_mask = pe.Node(interface=afni.Calc(),
                              name='anat_brain_mask')
    anat_brain_mask.inputs.expr = 'step(a)'
    anat_brain_mask.inputs.outputtype = 'NIFTI_GZ'

    workflow.connect(anat_skullstrip, 'out_file',
                     anat_brain_mask, 'in_file_a')

    workflow.connect(anat_skullstrip, 'out_file',
                     anat_skullstrip_orig_vol, 'in_file_b')

    workflow.connect(anat_brain_mask, 'out_file',
                     output_node, 'brain_mask')

    workflow.connect(anat_skullstrip_orig_vol, 'out_file',
                     output_node, 'brain')

    return workflow


config_schema = Schema({
    'already_skullstripped': bool,
    'skullstrip_option': In(['AFNI', 'BET', 'niworkflows-ants']),
    'skullstrip_shrink_factor': float,
    'skullstrip_var_shrink_fac': bool,
    'skullstrip_shrink_factor_bot_lim': float,
    'skullstrip_avoid_vent': bool,
    'skullstrip_n_iterations': int,
    'skullstrip_pushout': bool,
    'skullstrip_touchup': bool,
    'skullstrip_fill_hole': int,
    'skullstrip_NN_smooth': int,
    'skullstrip_smooth_final': int,
    'skullstrip_avoid_eyes': bool,
    'skullstrip_use_edge': bool,
    'skullstrip_exp_frac': float,
    'skullstrip_push_to_edge': bool,
    'skullstrip_use_skull': bool,
    'skullstrip_perc_int': int,
    'skullstrip_max_inter_iter': int,
    'skullstrip_fac': int,
    'skullstrip_blur_fwhm': int,
})


# TODO type and schema validation of yaml configuration
def register_workflow(workflow: pe.Workflow, config, resource_pool: ResourcePool):
    try:
        config_schema(config)
    except MultipleInvalid as e:
        raise ValueError(f'Invalid config: {e}')

    # TODO where to put already-skullstripped handler
    if config['already_skullstripped'] or config['skullstrip_option'] != 'AFNI':
        return

    skullstrip_workflow = create_workflow()
    skullstrip_workflow.inputs.AFNI_options.set(
        shrink_factor=config.skullstrip_shrink_factor,
        var_shrink_fac=config.skullstrip_var_shrink_fac,
        shrink_fac_bot_lim=config.skullstrip_shrink_factor_bot_lim,
        avoid_vent=config.skullstrip_avoid_vent,
        niter=config.skullstrip_n_iterations,
        pushout=config.skullstrip_pushout,
        touchup=config.skullstrip_touchup,
        fill_hole=config.skullstrip_fill_hole,
        avoid_eyes=config.skullstrip_avoid_eyes,
        use_edge=config.skullstrip_use_edge,
        exp_frac=config.skullstrip_exp_frac,
        smooth_final=config.skullstrip_smooth_final,
        push_to_edge=config.skullstrip_push_to_edge,
        use_skull=config.skullstrip_use_skull,
        perc_int=config.skullstrip_perc_int,
        max_inter_iter=config.skullstrip_max_inter_iter,
        blur_fwhm=config.skullstrip_blur_fwhm,
        fac=config.skullstrip_fac,
        monkey=config.skullstrip_monkey,
    )

    resource_map = resource_pool.group_by(name='tag', key='anatomical')
    for resource_key, resource in resource_map.items():
        updated_resource_key = resource_key.with_strategy(skullstrip='afni')
        node = resource.workflow_node
        slot = resource.slot

        workflow.connect(node, slot, skullstrip_workflow, 'input_spec.in_file')
        resource_pool[updated_resource_key.with_tag('brain_mask')] = Resource(skullstrip_workflow,
                                                                              'output_spec.brain_mask')
        resource_pool[updated_resource_key.with_tag('brain')] = Resource(skullstrip_workflow,
                                                                         'output_spec.brain')
        resource_pool[updated_resource_key] = Resource(skullstrip_workflow, 'output_spec.out_file')
