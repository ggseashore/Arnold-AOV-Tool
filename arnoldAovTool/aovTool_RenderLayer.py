import sys

import maya.cmds as cmds
import aovs
from aovs import AOVInterface
from functools import partial

lightType = ('aiAreaLight', 'aiSkyDomeLight', 'spotLight', 'directionalLight', 'pointLight', 'aiMeshLight')

lightAovExp_01 = {
    'coat_direct': "C<RS'coat'><L.'{0}'>",
    'coat_indirect': "C<RS'coat'>[DSVOB].*<L.'{0}'>",
    'diffuse_direct': "C<RD><L.'{0}'>",
    'diffuse_indirect': "C<RD>[DSVOB].*<L.'{0}'>",
    'specular_direct': "C<RS[^'coat']><L.'{0}'>",
    'specular_indirect': "C<RS[^'coat']>[DSVOB].*<L.'{0}'>",
    'sss_direct': "C<TD><L.'{0}'>",
    'sss_indirect': "C<RS'coat'>[DSVOB].*<L.'{0}'>",
    'tansmission_direct': "C<TS><L.'{0}'>",
    'tansmission_indirect': "C<TS>[DSVOB].*<L.'{0}'>",
    'volume_direct': "CV<L.'{0}'>",
    'volume_indirect': "CV[DSVOB].*<L.'{0}'>",
}

lightAovExp_02 = {
    'RGBA': "C.*<L.'{0}'>",
    'coat': "C<RS'coat'>.*<L.'{0}'>",
    'diffuse': "C<RD>.*<L.'{0}'>",
    'specular': "C<RS[^'coat']>.*<L.'{0}'>",
    'sss': "C<TD>.*<L.'{0}'>",
    'tansmission': "C<TS>.*<L.'{0}'>",
    'volume': "CV.*<L.'{0}'>",
}

lightAovExp_03 = {
'n':'N', 'p':'P', 'z':'Z', 'ao':'AO', 'emission':'emission', 'diffuse_albedo':'diffuse_albedo','sss_albedo':'sss_albedo'
}

lightAovExp_04 = {
'crypto_asset':'crypto_asset', 'crypto_material':'crypto_material','crypto_object':'crypto_object'
}

uti_aovs = ('aiAOV_diffuse_albedo', 'aiAOV_emission', 'aiAOV_sss_albedo', 'aiAOV_AO', 'aiAOV_N', 'aiAOV_P', 'aiAOV_Z')

crypto = ('aiAOV_crypto_asset', 'aiAOV_crypto_material', 'aiAOV_crypto_object')

tabs = {
    1: lightAovExp_01,
    2: lightAovExp_02,
    3: lightAovExp_03,
    4: lightAovExp_04
}


def returnVislilityLight():
    lightShape = []
    for type_ in lightType:
        lights = cmds.ls(type=type_)
        for light in lights:
            transform = cmds.listRelatives(light, p=True, f=True)[0]
            if cmds.getAttr('%s.visibility' % transform) == 1:
                lightShape.append(light)
    return lightShape


def returnLightNode():
    sels = cmds.ls(sl=True)
    nodes = []
    for i in sels:
        node = cmds.listRelatives(i, c=True, f=True)[0]
        if cmds.nodeType(node) in lightType:
            nodes.append(node)
    return nodes


def returnActiveAOVs():
    index = cmds.tabLayout('aovTab', q=True, sti=True)
    aovs = tabs[index].keys()
    activeAOVs = []
    for i in aovs:
        if cmds.checkBox(i, v=True, q=True):
            activeAOVs.append(i)
    return activeAOVs


def setAOVsCheckBox(key=True, *args):
    index = cmds.tabLayout('aovTab', q=True, sti=True)
    aovs = tabs[index].keys()
    if key == True:
        for i in aovs:
            cmds.checkBox(i, v=True, e=True)
    else:
        for i in aovs:
            cmds.checkBox(i, v=False, e=True)


def returnLightAov():
    aovsSet = set()
    for type_ in lightType:
        lights = cmds.ls(type=type_)
        for lgt in lights:
            aovsSet.add(cmds.getAttr('%s.aiAov' % lgt))
    return aovsSet

def createCryptoNode():
    nodes = cmds.ls(type='cryptomatte')
    if not nodes:
        node = cmds.shadingNode('cryptomatte',au=True,ss=True)
        node = cmds.rename(node,'_aov_cryptomatte')
    else:
        node = nodes[0]
    return node

def createAONode():
    node = cmds.shadingNode('aiAmbientOcclusion',asShader=True,ss=True)
    cmds.setAttr('%s.samples'%node,5)
    return node

def addAOVs(*args):
    index = cmds.tabLayout('aovTab', q=True, sti=True)
    aovsSet = set()
    for type_ in lightType:
        lights = cmds.ls(type=type_)
        for lgt in lights:
            aovsSet.add(cmds.getAttr('%s.aiAov' % lgt))
    aov = AOVInterface()
    activeAOVs = returnActiveAOVs()
    if index < 3:
        for aov_ in aovsSet:
            for aovType in activeAOVs:
                if not cmds.objExists('aiAOV_%s_%s' % (aov_, aovType)):
                    aov.addAOV('%s_%s' % (aov_, aovType))
                    cmds.setAttr('aiAOV_%s_%s.enabled' % (aov_, aovType), 0)
                    cmds.setAttr('aiAOV_%s_%s.lightPathExpression' % (aov_, aovType),
                                 tabs[index][aovType].format(aov_), type='string')
    else:
        for aovType in activeAOVs:
            if 'crypto' in aovType:
                cryptoAov = 'aiAOV_%s' % (lightAovExp_04[aovType])
                if not cmds.objExists(cryptoAov):
                    aov.addAOV(lightAovExp_04[aovType])
                    node = createCryptoNode()
                    cmds.connectAttr('%s.outColor'%node,'%s.defaultValue'%cryptoAov,f=True)
                    cmds.setAttr('%s.enabled'%cryptoAov,0)
            elif 'AO' == lightAovExp_03[aovType]:
                aoAov = 'aiAOV_%s' % (lightAovExp_03[aovType])
                if not cmds.objExists(aoAov):
                    aov.addAOV(lightAovExp_03[aovType])
                    node = createAONode()
                    cmds.connectAttr('%s.outColor' % node, '%s.defaultValue' % aoAov, f=True)
                    cmds.setAttr('%s.enabled' % aoAov, 0)
            else:
                utiAov = 'aiAOV_%s'%lightAovExp_03[aovType]
                if not cmds.objExists(utiAov):
                    aov.addAOV(lightAovExp_03[aovType])
                    cmds.setAttr('%s.enabled' % utiAov, 0)


def createLightAOVsBySelect(*args):
    index = cmds.tabLayout('aovTab', q=True, sti=True)
    aov = AOVInterface()
    nodes = returnLightNode()
    aovsSet = set()
    for node in nodes:
        aovsSet.add(cmds.getAttr('%s.aiAov' % node))
    activeAOVs = returnActiveAOVs()
    if index < 3:
        for aov_ in aovsSet:
            for aovType in activeAOVs:
                if not cmds.objExists('aiAOV_%s_%s' % (aov_, aovType)):
                    aov.addAOV('%s_%s' % (aov_, aovType))
                    cmds.setAttr('aiAOV_%s_%s.enabled' % (aov_, aovType), 0)
                    cmds.setAttr('aiAOV_%s_%s.lightPathExpression' % (aov_, aovType),
                                 tabs[index][aovType].format(aov_), type='string')
    else:
        pass


def deleteAllLightAOVs(*args):
    aovs = cmds.ls(type='aiAOV')
    for aov_ in aovs:
        for name in lightAovExp_02.keys():
            if name in aov_:
                cmds.delete(aov_)


def deleteLightAOVsBySelect(*args):
    index = cmds.tabLayout('aovTab', q=True, sti=True)
    nodes = returnLightNode()
    aovSet = set()
    for node in nodes:
        aovSet.add(cmds.getAttr('%s.aiAov' % node))
    activeAOVs = returnActiveAOVs()
    if index < 3:
        for aov_ in aovSet:
            for aovType in activeAOVs:
                if cmds.objExists('aiAOV_%s_%s' % (aov_, aovType)):
                    cmds.delete('aiAOV_%s_%s' % (aov_, aovType))
    else:
        pass

def lightAovOverrides(*args):
    nodes = returnLightNode()
    aovSet = set()
    for node in nodes:
        aovSet.add(cmds.getAttr('%s.aiAov' % node))
    activeAOVs = returnActiveAOVs()
    for aov_ in aovSet:
        for aovType in activeAOVs:
            aovNode = 'aiAOV_%s_%s' % (aov_, aovType)
            if cmds.objExists(aovNode):
                cmds.editRenderLayerAdjustment('%s.enabled' % aovNode)
                cmds.setAttr('%s.enabled' % aovNode, 1)


def createUtiAovOverrides(*args):
    for aov in uti_aovs:
        if cmds.objExists(aov):
            cmds.editRenderLayerAdjustment('%s.enabled' % aov)
            cmds.setAttr('%s.enabled' % aov, 1)


def createCryptoAovOverrides(*args):
    for aov in crypto:
        if cmds.objExists(aov):
            cmds.editRenderLayerAdjustment('%s.enabled' % aov)
            cmds.setAttr('%s.enabled' % aov, 1)


def closeAllAOVs(*args):
    all_aovs = cmds.ls('aiAOV_*')
    for i in all_aovs:
        try:
            cmds.editRenderLayerAdjustment('%s.enabled' % i)
            cmds.setAttr('%s.enabled' % i, 0)
        except:
            cmds.setAttr('%s.enabled' % i, 0)


def aovWindow():
    aovs = lightAovExp_01.keys()
    hight = len(aovs) * 30 + 72
    if cmds.window('aov_window', exists=True, q=True):
        cmds.deleteUI('aov_window')
    win = cmds.window('aov_window', title='AOV Window', widthHeight=(350, hight))

    cmds.columnLayout()

    cmds.rowColumnLayout(nc=2)

    cmds.columnLayout()

    tab_01 = cmds.tabLayout('aovTab', innerMarginWidth=5, innerMarginHeight=5)
    child_01 = cmds.columnLayout()

    for i in sorted(aovs):
        cmds.columnLayout()
        if 'volume' not in i:
            cmds.checkBox(i, l='%s' % i, v=True, w=150, h=30)
        else:
            cmds.checkBox(i, l='%s' % i, v=False, w=150, h=30)
        cmds.setParent('..')
    cmds.setParent('..')

    child_02 = cmds.columnLayout()
    aovs = lightAovExp_02.keys()
    for i in sorted(aovs):
        cmds.columnLayout()
        if 'volume' not in i and 'RGBA' not in i:
            cmds.checkBox(i, l='%s' % i, v=True, w=150, h=30)
        else:
            cmds.checkBox(i, l='%s' % i, v=False, w=150, h=30)
        cmds.setParent('..')
    cmds.setParent('..')

    child_03 = cmds.columnLayout()
    aovs = lightAovExp_03.keys()
    for i in sorted(aovs):
        cmds.columnLayout()
        cmds.checkBox(i, l='%s' % i, v=True, w=150, h=30)
        cmds.setParent('..')
    cmds.setParent('..')

    child_04 = cmds.columnLayout()
    aovs = lightAovExp_04.keys()
    for i in sorted(aovs):
        cmds.columnLayout()
        cmds.checkBox(i, l='%s' % i, v=True, w=150, h=30)
        cmds.setParent('..')
    cmds.setParent('..')

    cmds.tabLayout(tab_01, edit=True, tabLabel=(
        (child_01, 'MUTI'), (child_02, 'SINGLE'), (child_03, 'UTI'), (child_04, 'CRYPTO')), w=250
                   )
    cmds.setParent('..')

    cmds.rowColumnLayout(nc=2)
    cmds.button('Open All', w=125, h=36, c=partial(setAOVsCheckBox, True))
    cmds.button('Close All', w=125, h=36, c=partial(setAOVsCheckBox, False))
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.columnLayout()
    cmds.button('Light AOVs Overrides', w=200, h=hight / 8, c=lightAovOverrides)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('UTI AOVs Overrides', w=200, h=hight / 8, c=createUtiAovOverrides)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Crypto AOVs Overrides', w=200, h=hight / 8, c=createCryptoAovOverrides)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Create All AOVs ', w=200, h=hight / 8, c=addAOVs)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Create Select Light AOVs', w=200, h=hight / 8, c=createLightAOVsBySelect)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Close All Light AOVs', w=200, h=hight / 8, c=closeAllAOVs)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Delete All Light AOVs', w=200, h=hight / 8, c=deleteAllLightAOVs)
    cmds.setParent('..')
    cmds.columnLayout()
    cmds.button('Delete select Light AOVs', w=200, h=hight / 8, c=deleteLightAOVsBySelect)
    cmds.setParent('..')
    cmds.setParent('..')
    cmds.showWindow()
