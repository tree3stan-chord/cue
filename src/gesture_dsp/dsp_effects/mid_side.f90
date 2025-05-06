module mid_side
  implicit none
contains

  subroutine mid_side_sub(inbuf, outbuf, vocal_gain, n)
    ! inbuf      : real(8) array of length 2*N  (interleaved stereo: 
    !              L,R,L(ol),R,...)
    ! outbuf     : real(8) array, same length, to receive processed sam-
    !              -ples
    ! vocal_gain : real(8) scalar in [0,1]
    !
    !f2py intent(in) :: inbuf, vocal_gain, n
    !f2py intent(out) :: outbuf
    !f2py depend(n) :: inbuf, outbuf
    integer, intent(in)  :: n
    real(8), intent(in)  :: inbuf(2*n)
    real(8), intent(out) :: outbuf(2*n)
    real(8), intent(in)  :: vocal_gain
    integer :: i
    real(8) :: L, R, mid, side, out

    do i = 1, n
      ! extract left and right channels of frame i
      L    = inbuf(2*(i-1) + 1)
      R    = inbuf(2*(i-1) + 2)

      ! capture the mids and stereo-only shite
      mid  = 0.5d0 * (L + R)
      side = 0.5d0 * (L - R)

      ! if gain is 1.0, both instrumentals and vocals (as mid)
      ! otherwise 0.0, just instrumental, hope all goes well ;)
      out  = side + vocal_gain * mid

      ! writeback the mixed sample to the bout uffa
      outbuf(2*(i-1) + 1) = out
      outbuf(2*(i-1) + 2) = out
    end do
  end subroutine mid_side_sub

end module mid_side