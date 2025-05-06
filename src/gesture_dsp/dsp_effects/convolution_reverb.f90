module convolution_reverb_mod
  implicit none
contains

  subroutine conv_reverb(input, ir, output, n, ir_len)
    integer, intent(in) :: n, ir_len
    real(8), intent(in) :: input(n), ir(ir_len)
    real(8), intent(out) :: output(n+ir_len-1)
    integer :: i, j

    output = 0.0
    do i = 1, n
      do j = 1, ir_len
        output(i+j-1) = output(i+j-1) + input(i) * ir(j)
      end do
    end do
  end subroutine conv_reverb
  
end module convolution_reverb_mod