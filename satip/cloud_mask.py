import glob
import math

import click
import structlog
from satpy import Scene

log = structlog.stdlib.get_logger()


class GenerateCloudMask:
    """
    Generate cloud masks using the Separation of Pixels using
    an Aggregated Rating over Canada (SPARC) algorithm [1].

    References:
        [1] Reto Stockli: 2013, The HelioMont Surface Solar Radiation Processing (2022 Version),
        ¨ Scientific Report MeteoSwiss, 93, 126 pp.

    """

    def __init__(self, file_dir):
        self.fpath = glob.glob(file_dir + "/*.nat")
        self.channels = [
            "HRV",
            "IR_016",
            "IR_039",
            "IR_087",
            "IR_097",
            "IR_108",
            "IR_120",
            "IR_134",
            "VIS006",
            "VIS008",
            "WV_062",
            "WV_073",
        ]

        self.scn = Scene(reader="seviri_l1b_native", filenames=self.fpath)
        self.scn.load(self.channels)

    def temperature_score(self, Tcf=None, Toffset=-5.0, Tscale=-0.4):
        """
        Calculates the temperature score (Tscore).

        Args:
            T10_8 (numpy.ndarray): Brightness temperature of the 10.8 µm thermal channel.
            Tcf (numpy.ndarray): Clear sky (cloud free) brightness temperature.
            Toffset (float): Offset term in the Tscore equation.
            Tscale (float): Scaling term in the Tscore equation.

        Returns:
            numpy.ndarray : Temperature score (Tscore) calculated using the formula:
                Tscore = (T10.8 - Tcf - Toffset) * Tscale

        """
        try:
            Tscore = (
                self.scn["IR_108"].values - Tcf - Toffset
            ) * Tscale  # Tcf yet to be calculated
            return Tscore
        except Exception as e:
            # model function code to be called
            log.error(
                "Tcf value to be calculated by fitting a model through the diurnal course."
            )
            raise e

    def brightness_score(self, pcf=None, Boffset=0.05, Bscale=60):
        """
        Calculates the brightness score (Bscore)

        Args:
            p (numpy.ndarray): Reflectance of the visible channel.
            pcf (numpy.ndarray): Cloud-free background reflectance.
            Boffset (float): Offset term in the Bscore equation.
            Bscale (int): Scaling term in the Bscore equation.

        Returns:
            numpy.ndarray : Brightness score (Bscore)

        """
        try:
            Bscore = (
                self.scn["HRV"].values - Boffset
            ) * Bscale  # pcf yet to be calculated
            return Bscore
        except Exception as e:
            # clear sky compositing function to be called
            log.error(
                f"pcf value to be calculated by fitting a model through the diurnal course.\n{e}"
            )
            return

    def reflectance_score(self, Roffset16=0.03, Rscale16=400):
        """
        Calculates the reflectance score (Rscore)

        Args:
            R006 (numpy.ndarray): Reflectance value from the first channel (0.6 µm).
            R016 (numpy.ndarray): Reflectance value from the second channel (1.6 µm).
            Roffset16 (float): Offset term in the Rscore equation.
            Rscale16 (int): Scaling term in the Rscore equation.

        Returns:
            numpy.ndarray : Reflectance score (Rscore)

        """
        try:
            Rscore = (
                (
                    (
                        ((self.scn["VIS006"].values) ** 2)
                        * ((self.scn["IR_016"].values) ** 2)
                    )
                    / (
                        1.5
                        * ((self.scn["IR_016"].values) ** 2.8)
                        * (
                            3.0 * (self.scn["IR_016"].values)
                            + 0.5 * (self.scn["VIS006"].values)
                            + 3.5
                        )
                        + 1.5 * ((self.scn["VIS006"].values) ** 2)
                    )
                )
                - Roffset16
            ) * Rscale16
            return Rscore
        except Exception as e:
            log.warn(
                f"Unable to calculate Refletance Score: Reflectance(VIS 0.6 µm) and\
                Brightness Temperature(IR 1.6 µm) values are invalid.\n{e}"
            )
            return

    def simple_ratio_score(self, Noffset=0.1, Nscale=-30):
        """
        Calculates the simple ratio score (Nscore)

        Args:
            N (numpy.ndarray): Simple ratio value.
            Noffset (float): Offset term in the Nscore equation.
            Nscale (int): Scaling term in the Nscore equation.

        Returns:
            numpy.ndarray: Simple ratio score (Nscore)

        """
        try:
            Nscore = (
                abs(((self.scn["VIS008"].values) / (self.scn["VIS006"].values)) - 1)
                - Noffset
            ) * Nscale
            return Nscore
        except Exception as e:
            log.warn(
                f"Unable to calculate Simple Ratio score: \
                Reflectance(VIS 0.6 µm,0.8 µm) values are invalid.\n{e}"
            )
            return

    def stt_score(self, offset=5.0, scale=0.5):
        pass

    def cirrus_score(self, Coffset=1.5, Cscale=4.0):
        """
        Calculates the cirrus score (Cscore)

        Args:
            C (numpy.ndarray): Simple ratio value.
            Coffset (float): Offset term in the Nscore equation.
            Cscale (float): Scaling term in the Nscore equation.

        Returns:
            numpy.ndarray: Cirrus score (Cscore)

        """
        try:
            Cscore = (
                self.scn["IR_108"].values - self.scn["IR_120"].values - Coffset
            ) * Cscale
            return Cscore
        except Exception as e:
            log.warn(
                f"Unable to calculate Cirrus score:\
                Brightness Temperature (IR 10.8 µm,12.0 µm)values are invalid.\n{e}"
            )
            return

    def tt_score(self, offset, scale):
        pass

    def dt_score(self, offset, scale):
        pass

    def ndsi_score(self, Soffset=0.4, Sscale=40):
        """
        Calculates the  Normalized Difference Snow Index(NDSI) score (Sscore)

        Args:
            R016 (numpy.ndarray): Reflectance value from the Visible channel (1.6 µm).
            R006 (numpy.ndarray): Reflectance value from the Visible channel (0.6 µm).
            Soffset (float): Offset term in the Nscore equation.
            Sscale (int): Scaling term in the Nscore equation.

        Returns:
            numpy.ndarray: NDSI score (Sscore)

        """
        try:
            Sscore = (
                (
                    ((self.scn["VIS006"].values) - (self.scn["IR_016"].values))
                    / ((self.scn["VIS006"].values) + (self.scn["IR_016"].values))
                )
                - Soffset
            ) * Sscale
            return Sscore
        except Exception as e:
            log.warn(
                f"Unable to calculate NDSI score:\
                Reflectance (VIS 1.6 µm, IR 0.6 µm) values are invalid.{e}"
            )
            return

    def freeze_score(self, Foffset=-5.0, Fscale=1.0):
        """
        Calculates the Freeze Score (Fscore)

        Args:
            T10_8 (numpy.ndarray): Brightness temperature of the 10.8 µm thermal channel.
            Foffset (float): Offset term in the Nscore equation.
            Fscale (float): Scaling term in the Nscore equation.

        Returns:
            numpy.ndarray: Freeze score (Fscore)

        """
        try:
            date = self.scn["IR_108"].attrs["start_time"]
            day_of_year = int(date.strftime("%j"))
            Tf = 273.13 + 2 * math.sin(
                ((2 * day_of_year * math.pi) / 365.25) - (math.pi / 10)
            )
            Fscore = (-abs((self.scn["IR_108"].values) - Tf + 2) - Foffset) * Fscale
            return Fscore
        except Exception as e:
            log.warn(
                f"Unable to calculate Freeze score:\
                Brightness Temperature values(10.8 µm) are invalid.{e}"
            )
            return


@click.command()
@click.option(
    "--file-dir",
    default="./data",
    help="Where native file is stored ",
    type=click.STRING,
)
def run_cloud_mask(file_dir):
    cloud_mask_generator = GenerateCloudMask(file_dir)


if __name__ == "__main__":
    run_cloud_mask()
