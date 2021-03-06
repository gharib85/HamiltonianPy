def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config=Configuration('QuantumNumber',parent_package,top_path)
    config.add_extension('fpermutation',['fpermutation.f90'])
    config.add_subpackage('test')
    return config

if __name__ == '__main__':
    from numpy.distutils.core import setup
    setup(configuration=configuration)
