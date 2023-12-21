dataset_info = dict(
    dataset_name='mtuv1',
    paper_info=dict(
        author='Jeremias Baur',
        title='MTU length calculation',
        container='ETHZ',
        year='2023',
        homepage='',
    ),
    keypoint_info={
        0:
        dict(name='L_FM5', id=0, color=[51, 153, 255], type='lower', swap=''),
        1:
        dict(
            name='L_FCC',
            id=1,
            color=[51, 153, 255],
            type='lower',
            swap=''),
    },
    skeleton_info={},
    # the joint_weights is modified by MMPose Team
    joint_weights=[
        1.2, 1.
    ],

    # 'https://github.com/Fang-Haoshu/Halpe-FullBody/blob/master/'
    # 'HalpeCOCOAPI/PythonAPI/halpecocotools/cocoeval.py#L245'
    sigmas=[
        0.079,
        0.079,
    ])