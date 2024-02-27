_base_ = ['mmpose::_base_/default_runtime.py']

# common setting
num_keypoints = 2
input_size = (192, 256)

# runtime
max_epochs = 2000
stage2_num_epochs = 30
base_lr = 4e-3
train_batch_size = 128
val_batch_size = 64

train_cfg = dict(max_epochs=max_epochs, val_interval=10)
randomness = dict(seed=21)

# optimizer
optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=base_lr, weight_decay=0.0),
    clip_grad=dict(max_norm=35, norm_type=2),
    paramwise_cfg=dict(
        norm_decay_mult=0, bias_decay_mult=0, bypass_duplicate=True,
        custom_keys={'backbone':dict(lr_mult=0, decay_mult=0)}
        ),)

# learning rate
param_scheduler = [
    dict(
        type='LinearLR',
        start_factor=1.0e-5,
        by_epoch=False,
        begin=0,
        end=500),
    dict(
        type='CosineAnnealingLR',
        eta_min=base_lr * 0.05,
        begin=max_epochs // 4,
        end=max_epochs,
        T_max=max_epochs // 2,
        by_epoch=True,
        convert_to_iter_based=True),
]

# automatically scaling LR based on the actual training batch size
auto_scale_lr = dict(base_batch_size=64)

# codec settings
codec = dict(
    type='SimCCLabel',
    input_size=input_size,
    sigma=(4.9, 5.66),
    simcc_split_ratio=2.0,
    normalize=False,
    use_dark=False)

# model settings
model = dict(
    type='TopdownPoseEstimator',
    data_preprocessor=dict(
        type='PoseDataPreprocessor',
        mean=[123.675, 116.28, 103.53],
        std=[58.395, 57.12, 57.375],
        bgr_to_rgb=True),
    backbone=dict(
        _scope_='mmdet',
        type='CSPNeXt',
        arch='P5',
        expand_ratio=0.5,
        deepen_factor=0.33,
        widen_factor=0.5,
        out_indices=(4, ),
        channel_attention=True,
        norm_cfg=dict(type='SyncBN'),
        act_cfg=dict(type='SiLU'),
        init_cfg=dict(
            type='Pretrained',
            prefix='backbone.',
            checkpoint='https://download.openmmlab.com/mmpose/v1/projects/'
            'rtmposev1/rtmpose-s_simcc-body7_pt-body7_420e-256x192-acd4a1ef_20230504.pth'  # noqa
        )),
    head=dict(
        type='RTMCCHead',
        in_channels=512,
        out_channels=num_keypoints,
        input_size=input_size,
        in_featuremap_size=tuple([s // 32 for s in input_size]),
        simcc_split_ratio=codec['simcc_split_ratio'],
        final_layer_kernel_size=7,
        gau_cfg=dict(
            hidden_dims=256,
            s=128,
            expansion_factor=2,
            dropout_rate=0.,
            drop_path=0.,
            act_fn='SiLU',
            use_rel_bias=False,
            pos_enc=False),
        loss=dict(
            type='KLDiscretLoss',
            use_target_weight=True,
            beta=10.,
            label_softmax=True),
        decoder=codec),
    test_cfg=dict(flip_test=True))

# base dataset settings
# supply the path to your coco dataset
dataset_type = 'CocoDataset'
data_mode = 'topdown'
data_root = '/usr/scratch/vilan1/bsc23h2/data/processed/coco_datasets/treadmill/treadmill_v2/'

backend_args = dict(backend='local')

# pipelines
train_pipeline = [
    dict(type='LoadImage', backend_args=backend_args),
    dict(type='GetBBoxCenterScale'),
    #dict(type='RandomFlip', direction='horizontal'),
    #dict(type='RandomHalfBody'),
    dict(
        type='RandomBBoxTransform', scale_factor=[0.6, 1.4], rotate_factor=80),
    dict(type='TopdownAffine', input_size=codec['input_size']),
    dict(type='PhotometricDistortion'),
    dict(
        type='Albumentation',
        transforms=[
            dict(type='Blur', p=0.1),
            dict(type='MedianBlur', p=0.1),
            dict(
                type='CoarseDropout',
                max_holes=1,
                max_height=0.4,
                max_width=0.4,
                min_holes=1,
                min_height=0.2,
                min_width=0.2,
                p=1.0),
        ]),
    dict(
        type='GenerateTarget',
        encoder=codec,
        use_dataset_keypoint_weights=True),
    dict(type='PackPoseInputs')
]
val_pipeline = [
    dict(type='LoadImage', backend_args=backend_args),
    dict(type='GetBBoxCenterScale'),
    dict(type='TopdownAffine', input_size=codec['input_size']),
    dict(type='PackPoseInputs')
]

train_pipeline_stage2 = [
    dict(type='LoadImage', backend_args=backend_args),
    dict(type='GetBBoxCenterScale'),
    #dict(type='RandomFlip', direction='horizontal'),
    #dict(type='RandomHalfBody'),
    dict(
        type='RandomBBoxTransform',
        shift_factor=0.,
        scale_factor=[0.6, 1.4],
        rotate_factor=80),
    dict(type='TopdownAffine', input_size=codec['input_size']),
    dict(
        type='Albumentation',
        transforms=[
            dict(type='Blur', p=0.1),
            dict(type='MedianBlur', p=0.1),
            dict(
                type='CoarseDropout',
                max_holes=1,
                max_height=0.4,
                max_width=0.4,
                min_holes=1,
                min_height=0.2,
                min_width=0.2,
                p=0.5),
        ]),
    dict(
        type='GenerateTarget',
        encoder=codec,
        use_dataset_keypoint_weights=True),
    dict(type='PackPoseInputs')
]

# mapping

coco_mtu = [(i,i) for i in range(2)]

# train datasets
# supply the path to the train dataset
dataset_mtu = dict(
    type=dataset_type,
    data_root=data_root,
    data_mode=data_mode,
    ann_file='/usr/scratch/vilan1/bsc23h2/data/processed/coco_datasets/treadmill/treadmill_v2/train.json',
    data_prefix=dict(img='/usr/scratch/vilan1/bsc23h2/data/processed/coco_datasets/treadmill/treadmill_v2/images/'),
    pipeline=[
        dict(
            type='KeypointConverter',
            num_keypoints=num_keypoints,
            mapping=coco_mtu)
    ],
)

# data loaders
train_dataloader = dict(
    batch_size=train_batch_size,
    num_workers=5,
    pin_memory=True,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type='CombinedDataset',
        # if it doesn't work with a relative path, just supply the absolute path
        metainfo=dict(from_file='/home/bsc23h2/BA/mtu_walk_run_tri/mmpose/mmpose/configs/_base_/datasets/mtu.py'),
        datasets=[
            dataset_mtu,
        ],
        pipeline=train_pipeline,
        test_mode=False,
))

# val datasets
# supply the path to the train dataset
val_coco = dict(
    type=dataset_type,
    data_root=data_root,
    data_mode=data_mode,
    ann_file='/usr/scratch/vilan1/bsc23h2/data/processed/coco_datasets/treadmill/treadmill_v2/val.json',
    data_prefix=dict(img='/usr/scratch/vilan1/bsc23h2/data/processed/coco_datasets/treadmill/treadmill_v2/images/'),
    pipeline=[
        dict(
            type='KeypointConverter',
            num_keypoints=num_keypoints,
            mapping=coco_mtu)
    ],
)

val_dataloader = dict(
    batch_size=val_batch_size,
    num_workers=5,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type='DefaultSampler', shuffle=False, round_up=False),
    dataset=dict(
        type='CombinedDataset',
        # if it doesn't work with a relative path, just supply the absolute path
        metainfo=dict(from_file='/home/bsc23h2/BA/mtu_walk_run_tri/mmpose/mmpose/configs/_base_/datasets/mtu.py'),
        datasets=[
            val_coco,
        ],
        pipeline=val_pipeline,
        test_mode=True,
))

test_dataloader = val_dataloader

# hooks
default_hooks = dict(
    checkpoint=dict(save_best='AUC', rule='greater', max_keep_ckpts=1))

custom_hooks = [
    dict(
        type='EMAHook',
        ema_type='ExpMomentumEMA',
        momentum=0.0002,
        update_buffers=True,
        priority=49),
    dict(
        type='mmdet.PipelineSwitchHook',
        switch_epoch=max_epochs - stage2_num_epochs,
        switch_pipeline=train_pipeline_stage2)
]

# evaluators
test_evaluator = [dict(type='PCKAccuracy', thr=0.1), dict(type='AUC')]
val_evaluator = test_evaluator