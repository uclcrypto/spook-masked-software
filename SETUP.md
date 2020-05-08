# Reproduce the measurement setup

## Hardware requirements
In order to use a low-cost platform, we have decided to use a STMicroelectronics Discovery board. The version used for this ctf is based on the [STM32F030R8](https://www.st.com/content/st_com/en/products/microcontrollers-microprocessors/stm32-32-bit-arm-cortex-mcus/stm32-mainstream-mcus/stm32f0-series/stm32f0x0-value-line/stm32f030r8.html) with an ARM Cortex-M0. The configuration we have adopted is the _HSE oscillator on-board from X2 crystal (not provided)_, reported at page 17 of the [user manual of the board](https://www.st.com/resource/en/user_manual/dm00092306-discovery-kit-for-stm32f030-value-line-microcontrollers-stmicroelectronics.pdf). The list of modifications we have applied to the board are listed as follows:
*    In X2, a 8MHz quartz [crystal](https://be.farnell.com/txc/9b-8-000maaj-b/xtal-8-000mhz-18pf-hc-49s/dp/1842268?ost=crystal+9B-8.000MAAJ-B) has been soldered. We have used a through-hole type component. Following the user manual and the schematic, we have used a 18pF capacitors for C13 and C14. The resistor R23 is zero ohm and R22 is 390 ohms. In addition, we have removed solder bridges SB16, SB17 and SB18.
*    To increase the available bandwidth at the probing point, we have removed C18, C19, C20, C21. In addition, L1 has been substituted with a 0ohm resistor.

Once these modifications are done, one can plug the board in the following way:
1. **UART**: The board and the computer communicates through an external UART interface. Namely, an [UM232R](https://www.ftdichip.com/Support/Documents/DataSheets/Modules/DS_UM232R.pdf) is connected to the board with TX and RX being respectively PA9 and P10. On this point, any other UART modules will work.
2. **Clock**: The device is clocked at its maximum frequency of 48MHz.
3. **Trigger**: Before each encryption or decryption of Spook, the pin PB13 is set high. Afterwards, the pin is set to low. Hence, an oscilloscope should be triggered on the a rising edge of this signal.
4. **Probe**: The probe we have used is a CT1 that is placed on the second jumper (JP2).

To run the project, several packages have to be installed. The following instructions are dedicated to Ubuntu but could be transposed to other linux distributions:

```
sudo pip install pyserial numpy
```
The ARM tool chain is installed following [this link](https://blog.podkalicki.com/how-to-compile-and-burn-the-code-to-stm32-chip-on-linux-ubuntu/). In short, it requires to run:
```
sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi

```
and the device is flashed and debugged with openocd:
```
sudo apt-get install openocd
```

### Parameters
The crypto library can be compiled with many options. Next, several compilation flags are detailed.
1. `MASKING=1` means the masking is implemented. In this case, the inverse of clyde is also used for decryption. Please refer to [Spook website](https://spook.dev/) for more details.
2. `D=X` is the number of shares. It is used only if `MASKING` is set to 1.
3. `USE_ASM=1` is set if the shares are manipulated using assembly code. The project contains C and ASM code for many critical functions in utils_masking_asm.S. This flag makes use of the ASM version.
4. `BOARD=1` builds all the operating system used by the board. It generates a .elf that can be burn to the chip.
5. `DEBUG=1` debug mode is set.

As an example, to flash the board with masked implementation with 4 shares and assembly code, the following command is used:
```
make D=4 USE_ASM=1 BOARD=1 board burn
```
This generates the file [parameters.py](interface/parameters.py). It will later be used by the interface (i.e. to recover the number of shares).

### Functional Testing Scripts
The project contains testing scripts for the primary candidate of Spook. These are checking that the ciphertext matches the test vectors coming with the reference implementation of Spook. It also verifies the consistency of the decryption.
The on-board tests can be launched thanks to
```
make BOARD=1 test_board
```
where all the previously mentioned flags can be used. This will launch scripts within [test/](test/)

### Measurement Scripts

An example using a Picoscope is available in [capture.py](capture/capture.py). It provides the MCU with a masked key and additional inputs. Internally, the device will run a batch of encryptions with fresh inputs. The capture scripts derives these inputs with the function dev.unroll(N) and store then in a trace file. Then a simulation of the chip is available in [spook_masked.py](interface/spook_masked.py). As an example, one can run
```
python3 capture.py -b 1000 -n 4000 -k 1

```
This will capture 4000 traces where a batch of 1000 traces are recorded at once with a fixed key (-k 1).

This file and all the figures used are licensed under a [Creative Commons Attribution 4.0 International
License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg

